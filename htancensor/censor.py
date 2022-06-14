import tifftools
import os
import shutil
import re
import datetime
import argparse
import sys
import logging
import pathlib

def parse_args():
    parser = argparse.ArgumentParser(
        description="Redact tiff based file",
    )
    parser.add_argument(
        "input", 
        help="TIFF file to process"
    )
    parser.add_argument(
        "--output",
        #required=True,
        help="Path to the file to output"
    )
    parser.add_argument(
        "--dryrun",
        "--overwrite",
        default=False,
        action = "store_true",
        help="Just print information on the run, do not write file"
    )
    parser.add_argument(
        "--remove_date",
        default=False,
        action = "store_true",
        help=f"Remove DateTime 306 (0x132) and Date/Time values in Aperio SVS"
    )
    parser.add_argument(
        "--replace_date",
        help="YYYY:MM:DD HH:MM:SS string to replace all DateTime 306 (0x132) values and Date/Time values in Aperio SVS"
        "Note the use of colons in the date, as required by the TIFF standard.",
    )
    args = parser.parse_args()

    if args.remove_date:
        args.replace_date = None

    assert pathlib.Path(args.input).suffix == pathlib.Path(args.output).suffix, \
        "Output should have the same extension as the input"


    return args

def check_format(
    info:dict
) -> str:
    try:
        description = info['ifds'][0]['tags'][tifftools.Tag.IMAGEDESCRIPTION.value]['data']
    except:
        logging.info('No ImageDescription in IFD 0')
        description = "unknow"
    if description[:7] == 'Aperio ':
        logging.info("Aperio format found")
        format = "aperio"
    elif description[-4:] == 'OME>':
        logging.info("OME-TIFF format found")
        format = "ometiff"
    else:
        format = "unknown"
    return format

def remove_tag(
    info:dict,
    tag:tifftools.Tag,
    replacement:None
) -> dict:

    count = 0

    for idx, ifd in enumerate(tifftools.commands._iterate_ifds(info['ifds'], subifds = True)):
        for tagidx, taginfo in list(ifd['tags'].items()):
            if tagidx == tag.value:
                if replacement is None:
                    logging.info(f'Removing {tifftools.Tag.DATETIME} [{taginfo["data"]}] from IFD {idx}')
                    del ifd['tags'][tagidx]
                    count = count + 1
                else:
                    logging.info(f'Replacing DateTime tag (306) [{taginfo["data"]}] from IFD {idx} with [{replacement}]')
                    taginfo['datatype'] = tag.datatype
                    taginfo['data'] = replacement
                    count = count + 1

    if count > 0:    
        logging.info(f'{count} occurances of {tag} replaced with {replacement}')
    if count == 0:
         logging.info(f'No DateTime tags found')

    return info


def redact_tiff_date(
    info:dict,
    replacement:str
) -> dict:

    if replacement != None:
        assert len(replacement) == 19, \
            "length of DateTime string must be exactly 19 in format YYYY:MM:DD HH:MM:SS"

    info = remove_tag(info, tifftools.Tag.DATETIME,replacement)

    return info

def redact_aperio_date(
    info:dict,
    replacement:str
) -> dict:

    if replacement != None:
        assert len(replacement) == 19, \
            "length of DateTime string must be exactly 19 in format YYYY:MM:DD HH:MM:SS"

        replacement = replacement.split(" ")
        replacement[0] = replacement[0].replace(":","/")

    count = 0

    for idx, ifd in enumerate(tifftools.commands._iterate_ifds(info['ifds'])):
        for tagidx, taginfo in list(ifd['tags'].items()):
            if tagidx == tifftools.Tag.IMAGEDESCRIPTION.value:
                if replacement is None:
                    logging.info(f'Removing Date and Time from {tifftools.Tag.IMAGEDESCRIPTION} from IFD {idx}')
                    new_description =  re.sub(r'|Date = \d{2}/\d{2}/\d{2}|Time=\d{2}:\d{2}:\d{2}', '', taginfo['data'])
                else:
                    logging.info(f'Replacing Date and Time from {tifftools.Tag.IMAGEDESCRIPTION} from IFD {idx} with {replacement}')
                    new_description =  re.sub(r'Date = \d{2}/\d{2}/\d{2}', f'Date = {replacement[0]}',taginfo['data'])
                    new_description =  re.sub(r'Time = \d{2}:\d{2}:\d{2}', f'Time = {replacement[1]}', taginfo['data'])
                taginfo['datatype'] = tifftools.Datatype.ASCII
                taginfo['data'] = replacement
                count = count + 1

    if count > 0:    
        logging.info(f'{count} Aperio Dates and Times replaced with {replacement}')
    if count == 0:
         logging.info(f'No DateTime tags found')

def main():

    args = parse_args()

    try:
        info = tifftools.read_tiff(args.input)
    except: 
        logging.error('tifftools failed to load image. Provide a valid file')
        sys.exit(1)

    format = check_format(info)

    info = redact_tiff_date(info, args.replace_date)
    
    if format == "aperio":
        logging.info("Looking for dates in Aperio formatted ImageDescription")
        info = redact_aperio_date(info, args.replace_date)

    #if args.overwrite:
    #    tifftools.write_tiff(info, args.input, allowExisting=True)
    #else:
    #    tifftools.write_tiff(info, args.output)
    if args.dryrun:
        logging.info("Dry run. Output not saved")
    else:
        tifftools.write_tiff(info, args.output)

if __name__ == "__main__":
    main()