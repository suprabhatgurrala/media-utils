# extract_sup_timecode
Extract timecodes from .sup subtitle files and output to SRT. Useful for syncing existing SRT subtitles with .sup files.

PGS / .sup parsing code taken from https://github.com/EzraBC/pgsreader

# Usage
No dependencies are required, simply call the file `python3 extract_sup_timecodes.py [PATH]` and provide a path to a `.sup` file or directory with `.sup` files for batch processing.

```bash
usage: extract_sup_timecodes.py [-h] path

Extract timecodes from a .sup file and output into a .srt file.

positional arguments:
  path        Path to .sup file or directory containing .sup files.

options:
  -h, --help  show this help message and exit
```
