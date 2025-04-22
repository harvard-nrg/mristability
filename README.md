`mristability.py` will crawl over a directory of Siemens MRI Stability report files, read each report file, transform it to JSON, and write the transformed data to stdout in a way that is consumable by Telegraf using the [json_v2](https://docs.influxdata.com/telegraf/v1/data_formats/input/json_v2/) input data format.

# Requirements
`mristability.py` is self-contained Python script (Python 3.4+) with no external dependencies.

# Usage
> [!Tip]
> You can specify the base directory using the `--base-dir` argument or the `BASEDIR` environment variable.

```console
mristability.py --base-dir /path/to/stability/reports
```

# Telegraf
The included `mristability.toml` file is a [Telegraf input exec](https://www.influxdata.com/blog/plugin-spotlight-exec-execd/#heading0) configuration file.

This configuration file defines how to execute `mristability.py` and consume its output using the Telegraf  
[json_v2](https://docs.influxdata.com/telegraf/v1/data_formats/input/json_v2/) input data format.
