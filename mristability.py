#!/usr/bin/env -S python3 -u

import re
import os
import sys
import json
import time
import logging
from pathlib import Path
from argparse import ArgumentParser
from logging.handlers import RotatingFileHandler

class StabilityCollectorError(Exception):
    pass

class StabilityCollector:
    def __init__(self, base_dir, archive=False, verbose=False):
        self._base_dir = Path(base_dir)
        self._verbose = verbose
        self._archive = archive
        self._archive_dir = 'Processed'
        self._scanner = ('Harvard', 'Northwest', 'Bay1')
        self._file_pattern = re.compile(
            r'Stability_([0-9]{4}-[0-9]{2}-[0-9]{2}'
            r'T[0-9]{2}-[0-9]{2}-[0-9]{2}).txt'
        )
        self._files = list()
        # configure loggers
        self._log = logging.getLogger('mristability')
        self._log_file = self._base_dir / 'mristability.log'
        self._log_file_max_bytes = 100000000
        self._log_file_backup_count = 10
        self._configure_logger()

    def _configure_logger(self):
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
        )
        self._log.setLevel(logging.DEBUG)
        # configure stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        self._log.addHandler(stream_handler)
        # configure rotating log file handler
        file_handler = RotatingFileHandler(
            self._log_file,
            maxBytes=self._log_file_max_bytes,
            backupCount=self._log_file_backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self._log.addHandler(file_handler)

    def collect(self):
        ''' scan directory, process each file, and yield transformed data '''
        scandir = self._base_dir / Path(*self._scanner)
        if not self._scan_for_files(scandir):
            self._log.info(f'no new files found in {scandir}')
            return
        for i,path in enumerate(self._files):
            try:
                yield self._process_file(path)
                self._archive_file(path)
            except Exception as e:
                self._log.exception(e)

    def _scan_for_files(self, path):
        ''' scan for stability report files '''
        files = list()
        for entry in path.iterdir():
            if self._file_pattern.match(entry.name):
                files.append(entry)
        if files:
            self._log.debug(files)
            self._files = files
            return True
        return False

    def _process_file(self, path):
        ''' transform a single stability report into json '''
        self._log.info(f'processing file {path}')
        # parse unix timestamp from file name
        epoch = self._parse_epoch(path)
        with open(path, 'r') as fo:
            # parse number of channels and lookup coil
            line_1 = fo.readline()
            try:
                expr = (
                    r'Stability configuration: 16 slices, 500 '
                    r'measurements, ([0-9]{2}) channels\n'
                )
                match = re.match(expr, line_1)
                if not match:
                    raise StabilityCollectorError(f'could not parse channels from file {path}')
                channel_no = match.group(1)
                coil = self._resolve_channels(channel_no)
            except (AttributeError, KeyError) as e:
                raise StabilityCollectorError(f'error "{e}" for file "{path}", line {line_1}')
            lines = fo.read()
            # divide document into sections
            expr = (
                r'Stability (.+?) results:\n\nslice#(.*)\n 1(.*)\n 2(.*)\n 3(.*)\n'
                r' 4(.*)\n 5(.*)\n 6(.*)\n 7(.*)\n 8(.*)\n 9(.*)\n10(.*)\n11(.*)\n12'
                r'(.*)\n13(.*)\n14(.*)\n15(.*)\n16(.*)\n'
            )
            # parse each section
            sections = re.findall(expr, lines, re.MULTILINE)
            scannerstr = '.'.join(self._scanner)
            data = {
                'scanner': scannerstr,
                'coil': coil,
                'filename': path.name,
                'timestamp': epoch
            }
            for section in sections:
                section = list(section)
                section_type = section.pop(0)
                headers = section.pop(0).split()
                headers = [hdr.replace('[%]', 'pct') for hdr in headers]
                headers = [re.sub(r'\W+', '', hdr) for hdr in headers]
                section = [block.split() for block in section]
                for i,row in enumerate(section, start=1):
                    row = map(float, row)
                    for key,value in zip(headers, row):
                        key = f'{scannerstr}.{coil}.{key}.{section_type}.{i}'
                        data[key] = value
        return data

    def _archive_file(self, source):
        ''' move file into archive directory so it is not processed again '''
        archive_dir = source.parent / self._archive_dir
        archive_dir.mkdir(parents=True, exist_ok=True)
        destination = archive_dir / source.name
        if self._archive:
            self._log.info(f'renaming {source} to {destination}')
            source.rename(destination)
        else:
            self._log.info(f'pass --archive to rename {source} to {destination}')

    def _resolve_channels(self, channels):
        ''' map number of receive channels to head coil '''
        channelmap = {
            '32': '32',
            '48': '64',
            '64': '64'
        }
        if channels not in channelmap:
            raise StabilityCollectorError(f'no coil mapped for number of channels {channels}')
        return channelmap[channels]

    def _parse_epoch(self, path):
        ''' parse unix timestamp from file name '''
        date_time = self._file_pattern.match(path.name).group(1)
        pattern = '%Y-%m-%dT%H-%M-%S'
        epoch = int(time.mktime(time.strptime(date_time, pattern)))
        self._log.debug(f'parsed epoch {epoch} from file {path.name}')
        assert(epoch)
        return epoch

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-b', '--base-dir', type=Path, 
        default=os.environ.get('BASEDIR'))
    parser.add_argument('-a', '--archive', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
   
    if not args.base_dir:
        parser.print_usage()
        print('mristability.py: error: the following arguments are required: -b/--base-dir')
        sys.exit(1)
        
    collector = StabilityCollector(
        base_dir=args.base_dir,
        archive=args.archive,
        verbose=args.verbose
    )

    data = list(collector.collect())
    print(json.dumps(data, indent=2))

