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
        "output",
        help="Path to the file to output"
    )
    parser.add_argument(
        "--dryrun",
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
        print('No ImageDescription in IFD 0')
        description = "unknow"
    if description[:7] == 'Aperio ':
        print("Aperio format found")
        format = "aperio"
    elif description[-4:] == 'OME>':
        print("OME-TIFF format found")
        format = "ometiff"
    else:
        format = "unknown"
    try: 
        tags = info['ifds'][0]['tags'][65449]
        format = "ndpi"
    except:
        pass
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
                    print(f'Removing {tifftools.Tag.DATETIME} [{taginfo["data"]}] from IFD {idx}')
                    del ifd['tags'][tagidx]
                    count = count + 1
                else:
                    print(f'Replacing DateTime tag (306) [{taginfo["data"]}] from IFD {idx} with [{replacement}]')
                    taginfo['datatype'] = tag.datatype
                    taginfo['data'] = replacement
                    count = count + 1

    if count > 0:    
        print(f'{count} occurances of {tag} replaced with {replacement}')
    if count == 0:
         print(f'No DateTime tags found')

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
                if re.match(r'.+\|Date = \d{2}\/\d{2}\/\d{2}.+',taginfo['data'], flags = re.S):
                    if replacement is None:
                        print(f'Removing Date and Time from {tifftools.Tag.IMAGEDESCRIPTION} from IFD {idx}')
                        new_description =  re.sub(r'\|Date = \d{2}\/\d{2}\/\d{2}\|Time = \d{2}:\d{2}:\d{2}', '', taginfo['data'])
                    else:
                        print(f'Replacing Date and Time from {tifftools.Tag.IMAGEDESCRIPTION} from IFD {idx} with {replacement}')
                        new_description =  re.sub(r'Date = \d{2}\/\d{2}\/\d{2}', f'Date = {replacement[0]}',taginfo['data'])
                        new_description =  re.sub(r'Time = \d{2}:\d{2}:\d{2}', f'Time = {replacement[1]}', taginfo['data'])
                    taginfo['datatype'] = tifftools.Datatype.ASCII
                    taginfo['data'] = new_description
                    count = count + 1

    if count > 0:    
        print(f'{count} Aperio Dates and Times replaced with {replacement}')
    if count == 0:
         print(f'No DateTime tags found')

    return info

def remove_ome_date(
    info:dict,
) -> dict:


    count = 0

    for idx, ifd in enumerate(tifftools.commands._iterate_ifds(info['ifds'])):
        for tagidx, taginfo in list(ifd['tags'].items()):
            if tagidx == tifftools.Tag.IMAGEDESCRIPTION.value:
                if re.match(r'.+\<AcquisitionDate\>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\<\/AcquisitionDate\>.+',taginfo['data'], flags = re.S):
                    print(f'Removing AcquisitionDate from {tifftools.Tag.IMAGEDESCRIPTION} from IFD {idx}')
                    new_description =  re.sub(r'\<AcquisitionDate\>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\<\/AcquisitionDate\>', '', taginfo['data'])
                    taginfo['datatype'] = tifftools.Datatype.ASCII
                    taginfo['data'] = new_description
                    count = count + 1

    if count > 0:    
        print(f'{count} OME AcquisitionDate attributes removed')
    if count == 0:
         print(f'No AcquisitionDate tags found')

    return info

def remove_ome_sa(
    info:dict,
) -> dict:


    count = 0

    for idx, ifd in enumerate(tifftools.commands._iterate_ifds(info['ifds'])):
        for tagidx, taginfo in list(ifd['tags'].items()):
            if tagidx == tifftools.Tag.IMAGEDESCRIPTION.value:
                if re.match(r'.+\<StructuredAnnotations\>.+\<\/StructuredAnnotations\>.+',taginfo['data'], flags = re.S):
                    print(f'Removing StructuredAnnotations from {tifftools.Tag.IMAGEDESCRIPTION} from IFD {idx}')
                    new_description =  re.sub(r'\<StructuredAnnotations\>.+\<\/StructuredAnnotations\>', '', taginfo['data'])
                    taginfo['datatype'] = tifftools.Datatype.ASCII
                    taginfo['data'] = new_description
                    count = count + 1

    if count > 0:    
        print(f'OME Structured annotations removed')
    if count == 0:
         print(f'OME Structured annotations notfound')

    return info


def main():

    args = parse_args()

    try:
        dirty_info = tifftools.read_tiff(args.input)
        info = dirty_info
    except Exception as e:
        print("The error raised is: ", e)
        sys.exit(1)

    format = check_format(info)

    n_ifds =  sum(1 for _ in tifftools.commands._iterate_ifds(info['ifds'], subifds = True))
    print(f'Searching accross {n_ifds} IFDs')

    info = redact_tiff_date(info, args.replace_date)
    
    if format == "aperio":
        print("Looking for dates in Aperio formatted ImageDescription")
        info = redact_aperio_date(info, args.replace_date)

    if format == "ometiff":
        print("Looking for dates in OME formatted ImageDescription")
        info = remove_ome_date(info)
        info = remove_ome_sa(info)

    #if args.overwrite:
    #    tifftools.write_tiff(info, args.input, allowExisting=True)
    #else:
    #    tifftools.write_tiff(info, args.output)

    #if dirty_info == info:
    #    print('No changes made. Output not saved')
    if args.dryrun:
        print("Dry run. Output not saved")
    else:
        tifftools.write_tiff(info, args.output)

if __name__ == "__main__":
    main()