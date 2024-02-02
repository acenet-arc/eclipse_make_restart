# `eclipse_make_restart`

This is a small helper tool that processes ECLIPSE/E300 data files `FILENAME.DATA` to prepare them to restart a simulation from the last set of `FILENAME.Xiiii` and `FILENAME.Siiii` report files.

```
$ ./eclipse_make_restart.py -h
usage: ./eclipse_make_restart.py [-h] [-b] [--restore] [-v] NAME[.DATA]

Updates an Eclipse DATA file for the next restart.

positional arguments:
  NAME[.DATA]    Name of the DATA file (needs to be the same for NAME.X0000 and NAME.S0000 files).

options:
  -h, --help     show this help message and exit
  -b, --backup   Backup DATA file as "NAME.DATA.BACKUP".
  --restore      Restore DATA file from "NAME.DATA.BACKUP" before processing.
  -v, --verbose  Show additional messages for debugging.
```