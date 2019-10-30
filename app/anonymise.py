#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This application is a use case from the EU-Brazil Atmosphere project. For more
information on the project, visit our website at https://www.atmosphere-eubrazil.eu/.
The original application is hosted at the project's GitHub repository at
https://github.com/eubr-atmosphere/radiomics.

Copyright: QUIBIM SL – Quantitative Imaging Biomarkers in Medicine - www.quibim.com
"""

import sys
import base64
import gcm_cipher
import getopt
import os
import numpy as np
import video_frames as vf
import view_classification as vc
import doppler_segmentation as ds
import texture_analysis as tex
import textures_classification as tc
import hashlib
import PIL.Image
import shutil
import rediswq
import requests
import socket
import swift
import tempfile
import threading
import zipfile

from collections import deque

import warnings
warnings.filterwarnings("ignore")

if "ENV_PATH" in os.environ:
    ENV_PATH = os.environ["ENV_PATH"]
else:
    ENV_PATH = "/env"

# After LEASE_SECS, an unfinished work item will
# return to the main queue (work to be done).
if "ITEM_LEASE_SECS" in os.environ:
    LEASE_SECS = int(os.environ["ITEM_LEASE_SECS"])
else:
    LEASE_SECS = 15

if "INPUT_FOLDER" in os.environ:
    INPUT_FOLDER = os.environ["INPUT_FOLDER"]
else:
    INPUT_FOLDER = "/input"

if "ENCRYPTION_KEY" not in os.environ:
    print("[ERROR] Encryption key not found! Exiting...")
    exit(1)

ENCRYPTION_KEY = base64.b64decode(os.environ["ENCRYPTION_KEY"])
upload_thread_deque = deque()


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for f in files:
            ziph.write(os.path.join(root, f), f)


def download_tempfile(url):
    """Download and decrypt a TemporaryFile object. This file must be closed by
    the user.

    @type url: str
    @param url: URL to download content
    @rtype: TemporaryFile
    @returns: a temporary file with URL content
    """
    global ENCRYPTION_KEY, INPUT_FOLDER

    # Download the file
    request = requests.get(url=url)

    # Write content to TemporaryFile object
    temp_file = tempfile.NamedTemporaryFile(dir=INPUT_FOLDER, suffix=".mp4")
    temp_file.write(gcm_cipher.decrypt(ENCRYPTION_KEY, None, request.content[:12], request.content[28:], request.content[12:28]))
    temp_file.flush()

    temp_file.seek(0)

    return temp_file


def get_env(env_name, default=None):
    global ENV_PATH

    if env_name in os.environ:
        return os.environ[env_name]

    try:
        env_file = open("%s/%s" % (ENV_PATH, env_name), 'r')
        content = env_file.read().splitlines()[0]
        env_file.close()
        
        return content
    except:
        return default


def extract_and_anonymise(videos_path,input_v,videos_path_out,output_v):
    vfull_in=os.path.join(videos_path, input_v)
    print('Extracting and anonymising: %s' % vfull_in)
    frames = vf.load_video(vfull_in)
    index = 0
    for fr in frames:
        dimy, dimx, depth = fr.shape
        for i in range(0,int(dimy/6)):
            for j in range(int(2*dimx/3)-10,dimx):
                fr[i][j][0]=0
                fr[i][j][1]=0
                fr[i][j][2]=0
                
        directory=os.path.join(videos_path_out, output_v)
        if not os.path.exists(directory):
            os.makedirs(directory)

        vfull_out=os.path.join(directory, str(index)+'.png')
        index = index+1
        imagen=PIL.Image.fromarray(fr)
        imagen.save(vfull_out, 'png')


def process_video(video_path, output_path):
    v = os.path.basename(video_path)
    file_path = video_path
    video_path = os.path.dirname(video_path)
    if not v.startswith('.') and v.lower().endswith('.mp4'):
        print('Check %s' % file_path)
        if vf.if_doppler(file_path):
            hash_object = hashlib.md5(file_path.encode())
            output_v=hash_object.hexdigest()
            extract_and_anonymise(video_path,v,output_path,output_v)
            
            return hash_object.hexdigest()
        else:
            return None


def handle_result(result, output_videos_path, results_container, queue):
    if result is not None:
        zip_filename = '%s/%s.zip' % (output_videos_path, result)
        zipf = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        zipdir('%s/%s/' % (output_videos_path, result), zipf)
        zipf.close()

        print("INFO:item completed. results posted.")
        swift.put_object(results_container, os.path.basename(zip_filename), open(zip_filename, 'r'))

        # delete output
        shutil.rmtree("%s/%s" % (output_videos_path, result))
        os.remove(zip_filename)

    else:
        queue.insert_queue("job:errors", url)


if __name__ == '__main__':
    try:
       opts, args = getopt.getopt(sys.argv[1:],"ho:",["help=","folder=","outputfolder="])

    except getopt.GetoptError:
       print('main.py -o <output videos folder>')
       sys.exit(2)

    for opt, arg in opts:
       print("opt: %s, arg: %s" % (opt, arg))
       if opt == '-h':
          print('main.py -o <output videos folder>')
          sys.exit()
       elif opt in ("-o", "--outputfolder"):
          output_videos_path = arg

#    print("Input dir: %s" % input_videos_path)
#    print("Output dir: %s" % output_videos_path)

    # get Redis address from environemnt.
    # defaults to 'redis:6379' using the queue 'job'.
    container_hostname = socket.gethostname()
    job_name = container_hostname[:container_hostname.rfind("-")]

    results_container = "%s-results" % (job_name)

    swift.create_public_container(results_container)

    redis_host = get_env('REDIS_HOST')
    redis_port = get_env('REDIS_PORT', 6379)
    redis_queue = get_env('REDIS_QUEUE', 'job')

    print('INFO:Trying to reach redis at "%s:%s". Using queue "%s".' %
          (redis_host, redis_port, redis_queue))
    queue = rediswq.RedisWQ(name=redis_queue, host=redis_host, port=redis_port)

    item_count = 0

    while not queue.empty():
        object_url = queue.lease(lease_secs=LEASE_SECS, block=True, timeout=2)
        if object_url is not None:
            url = object_url.decode("utf=8")
            print("retrieved item", url)
            # Download the item file
            job_item_file = download_tempfile(url)

            result = process_video(job_item_file.name, output_videos_path)
            
            # Close temporary file
            job_item_file.close()
            queue.complete(object_url)

            upload_thread = threading.Thread(target=handle_result, args=(result, output_videos_path, results_container, queue))
            upload_thread.start()
            upload_thread_deque.append(upload_thread)
        else:
            queue.check_expired_leases()
            print("INFO:waiting for work...")

    print("INFO:joining threads...")

    while len(upload_thread_deque) > 0:
        upload_thread_deque.pop().join()

    print("INFO:all threads joint")
