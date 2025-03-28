`mristability.py` will crawl over a directory of Siemens MRI Stability report files, read each report file, transform it to JSON, and write the transformed data to stdout (in a way that is easily consumable by Telegraf).

# Requirements
`mristability.py` is self-contained Python script that depends on Python 3.4+

# Usage
`mristability.py --base-dir /path/to/stability/reports`

# Telegraf
The included `mristability.toml` is a [Telegraf exec](https://www.influxdata.com/blog/plugin-spotlight-exec-execd/#heading0) configuration 
file.

This file defines how to execute `mristability.py` and consume its output as 
[JSON](https://docs.influxdata.com/telegraf/v1/data_formats/input/json/).
