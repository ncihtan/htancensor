import tifftools
import os
import shutil
import re
import datetime
import argparse
import sys
import logging

logging.basicConfig(
    level=logging.INFO
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Redact tiff based file",
    )
    parser.add_argument(
        "input", 
        help="TIFF file to process"
    )
    parser.add_argument(
        "--replace_date",
        help="YYYY:MM:DD HH:MM:SS string to replace all DateTime values."
        "Note the use of colons in the date, as required by the TIFF standard.",
    )
    output_group = parser.add_mutually_exclusive_group(required = True)
    output_group.add_argument(
        "--output",
        help="Path to the file to output"
    )
    output_group.add_argument(
        "--overwrite",
        default=False,
        action = "store_true",
        help="Boolean. If selecred overwrites the project"
    )
    args = parser.parse_args()
    return args

def check_format(
    info:dict
) -> str:
    description = info['ifds'][0]['tags'][tifftools.Tag.IMAGEDESCRIPTION.value]['data']
    if description[:7] == 'Aperio ':
        format = "aperio"
    elif description[-4:] == 'OME>':
        format = "ometiff"
    else:
        format = "unknown"
    return format

def redact_tiff_date(
    info:dict,
    replacement:str = "1970:01:01 00:00:00"
) -> dict:

    assert len(replacement) == 19, \
        "length of DateTime string must be exactly 19"

    tiff_dates = 0

    for i in range(len(info['ifds'])):
        try:
            # Check it exists
            info['ifds'][i]['tags'][tifftools.Tag.DATETIME.value]

            # If so replace
            info['ifds'][i]['tags'][tifftools.Tag.DATETIME.value] = {
                'data': str(replacement),
                'datatype': tifftools.Datatype.ASCII
            }

            tiff_dates = tiff_dates + 1
        except:
            continue
    if tiff_dates > 0:    
        logging.info(f'{tiff_dates} DateTime tags replaced with {replacement}')

    return info

    


def redact_aperio_date(
    info:dict,
    replacement:str = "01/01/70 00:00:00"
) -> dict:
    aperio_dates = 0
    for i in range(len(info['ifds'])):
        try: 
            ## Reset Dates In ImageDescription
            description = info['ifds'][i]['tags'][tifftools.Tag.IMAGEDESCRIPTION.value]
            value = description['data']
            value = re.sub(r'Date = \d{2}/\d{2}/\d{2}', 'Date = 01/01/70', value)
            value = re.sub(r'Time = \d{2}:\d{2}:\d{2}', 'Time = 00:00:00', value)

            assert len(value.encode('utf-8')) == len(description['data'].encode('utf-8')), \
                "New description must match length of old one"

            info['ifds'][i]['tags'][tifftools.Tag.IMAGEDESCRIPTION.value] = {
                'data': value,
                'datatype': tifftools.Datatype.ASCII
            }

            aperio_dates = aperio_dates + 1

        except:
            continue

    logging.info(f'{aperio_dates} dates replaced with {replacement}')

    return(info)


def main():
    args = parse_args()

    try:
        info = tifftools.read_tiff(args.input)
    except: 
        logging.error('tifftools failed to load image. Provide a valid file')
        sys.exit(1)

    format = check_format(info)

    info = redact_tiff_date(info)
    
    if format == "aperio":
        info = redact_aperio_date(info)

    if args.overwrite:
        tifftools.write_tiff(info, args.input, allowExisting=True)
    else:
        tifftools.write_tiff(info, args.output)



if __name__ == "__main__":
    main()