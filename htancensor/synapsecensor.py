# Passes a synapse entity into censor.py
from posixpath import basename
from sys import flags, stdout
from numpy import argsort
import synapseclient
from htancensor import *
import argparse
import os
import subprocess
import re

def parse_args():
    parser = argparse.ArgumentParser(
        description="Redact tiff based file. Will add as a new version of the synapse entity",
    )
    parser.add_argument(
        "input", 
        help="A synapse ID"
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

    return args

def main():
    args = parse_args()
    syn = synapseclient.Synapse()
    syn.login()

    entity = syn.get(args.input)

    output = os.path.basename(entity.path)

    censor_exc = subprocess.run(
        ['python','htancensor/censor.py', str(entity.path), '--output' , str(output),'--remove_date'], 
        capture_output = True, text=True
        )
    #print(censor_exc.stdout)
    print(censor_exc.stdout)

    if re.match(r'.+No changes made.+',censor_exc.stdout, flags = re.S):
        pass
    else:
        print(f"Uploading new version to {entity.id}")
        entity.path = output
        entity.versionComment = "de-identified with htancensor"
        syn.store(entity)


if __name__ == "__main__":
    main()