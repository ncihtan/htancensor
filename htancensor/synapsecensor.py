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
from urllib.parse import urlunparse
from urllib.parse import urlparse

import hashlib

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

def get_uri(
    entity:synapseclient.Entity
) -> str:
    handle = entity._file_handle
    if handle['concreteType'] == 'org.sagebionetworks.repo.model.file.S3FileHandle':
        scheme = 's3'
    if handle['concreteType'] == 'org.sagebionetworks.repo.model.file.GoogleCloudFileHandle':
        scheme = 'gs'
    bucket = handle['bucketName']
    key = handle['key']

    uri = urlunparse((scheme,bucket,key,'','',''))

    return uri

def md5_file(filename):
    hash_object = hashlib.md5()
 
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_object.update(chunk)
 
    return hash_object.hexdigest()

def gs_upload(filename, uri):
    hash = md5_file(filename)

    upload_cmd = ['gsutil', '-h', f'x-goog-meta-content-md5:{hash}', 'cp', filename, uri]
    upload_exc = subprocess.run(
        upload_cmd, 
        capture_output = True, text=True
        )

def syn_update(syn, filename, entity):
       syn.uploadFileHandle(filename, entity['parentId'])

#def htan_entity_update(entity,output):

    # Check storage location
    # If external in gs and created by 3413795 use gs_upload
    # If external in s3 and created by 3413795 use s3_upload
    # Otherwise update with syn.store


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

    uri = get_uri(entity)

    #print(f'source: {uri}')
    scratch_uri = uri.replace('gs://', 'gs://htan-dcc-scratch/htancensor/')
    print(f'Uploading to scratch: {scratch_uri}')
    gs_upload(output, uri)

    print('Cleaning up...')
    print('\tRemoving output')
    os.remove(output)
    print('\tRemoving from cache')
    subprocess.run(['rm', '-rf', entity.cacheDir])
    #if entity['createdBy'] == '3413795':
    #    if re.match(r'^gs\:\/\/htan-dcc.+', str(uri)):
    #        print(f'Updating in HTAN Google bucket: {uri}')
    #        gs_upload(output, uri)
    #else:
    #    if re.match(r'^gs\:\/\/htan-dcc.+', str(uri)):
    #        print('not trying to upload')
    # #       print(f'Updating in HTAN Google bucket via synapse,{entity["id"]}')
    # #       gs_upload(output, uri)
    ##        syn_update(syn, output, entity)


    #if re.match(r'^s3\:\/\/proddata.sagebase.org.+', uri):
    #    print('Synapse storage')
    #    syn_update(output,entity)

    #hash = md5_file(output)
    #print(hash)


    
    #if re.match(r'.+No changes made.+',censor_exc.stdout, flags = re.S):
    #    pass
    #else:
    #    print(f"Uploading new version to {entity.id}")
    #    entity.path = output
    #    entity.versionComment = "de-identified with htancensor"
    #    syn.store(entity)


if __name__ == "__main__":
    main()