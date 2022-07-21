# `htancensor`

`htancensor` provides methods for removal or replacement of tiff tags and ImageDescription contents that may present a risk of participant re-identification.

## Installation

Clone this repository, move into and install
```
git clone https://github.com/ncihtan/htancensor
cd htancensor
pip install -e .
```

## Example

```
htancensor example.svs --output clean.svs --replace_date "1970:01:01 00:00:00"
```

## Usage

```
usage: htancensor [-h] [--dryrun] [--remove_date] [--replace_date REPLACE_DATE] input output

Redact tiff based file

positional arguments:
  input                 TIFF file to process
  output                Path to the file to output

optional arguments:
  -h, --help            show this help message and exit
  --dryrun              Just print information on the run, do not write file
  --remove_date         Remove DateTime 306 (0x132) and Date/Time values in Aperio SVS, Acqisition date in OME-TIFF and all structuted annotations
  --replace_date REPLACE_DATE
                        YYYY:MM:DD HH:MM:SS string to replace all DateTime 306 (0x132) values and Date/Time values in Aperio SVSNote the use of colons in the date, as required by the TIFF standard.
```
 
 For files on synapse. CAUTION: Does not respect external storage locations. New versions will go onto Synapse storage

 ```
usage: htancensor-synapse [-h] [--dryrun] [--remove_date] [--replace_date REPLACE_DATE] input

Redact tiff based file. Will add as a new version of the synapse entity

positional arguments:
  input                 A synapse ID

optional arguments:
  -h, --help            show this help message and exit
  --dryrun              Just print information on the run, do not write file
  --remove_date         Remove DateTime 306 (0x132) and Date/Time values in Aperio SVS
  --replace_date REPLACE_DATE
                        YYYY:MM:DD HH:MM:SS string to replace all DateTime 306 (0x132) values and Date/Time values in Aperio SVSNote the use of colons in the date, as required by the TIFF
                        standard.
 ```
