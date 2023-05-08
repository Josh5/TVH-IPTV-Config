#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import subprocess


class FFProbeError(Exception):
    """
    FFProbeError
    Custom exception for errors encountered while executing the ffprobe command.
    """

    def __init___(self, path, info):
        Exception.__init__(self, "Unable to fetch data from file {}. {}".format(path, info))
        self.path = path
        self.info = info


def ffprobe_cmd(params):
    """
    Execute a ffprobe command subprocess and read the output
    :param params:
    :return:
    """
    command = ["ffprobe"] + params

    print(" ".join(command))

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()

    # Check for results
    try:
        raw_output = out.decode("utf-8")
    except Exception as e:
        raise FFProbeError(command, str(e))
    if pipe.returncode == 1 or 'error' in raw_output:
        raise FFProbeError(command, raw_output)
    if not raw_output:
        raise FFProbeError(command, 'No info found')

    return raw_output


def ffprobe_file(vid_file_path):
    """
    Returns a dictionary result from ffprobe command line prove of a file
    :param vid_file_path: The absolute (full) path of the video file, string.
    :return:
    """
    if type(vid_file_path) != str:
        raise Exception('Give ffprobe a full file path of the video')

    params = [
        "-loglevel", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-show_error",
        "-show_chapters",
        vid_file_path
    ]

    # Check result
    results = ffprobe_cmd(params)
    try:
        info = json.loads(results)
    except Exception as e:
        raise FFProbeError(vid_file_path, str(e))

    return info


def generate_iptv_url(config, url='', service_name=''):
    if not url.startswith('pipe://'):
        settings = config.read_settings()
        if settings['settings']['enable_stream_buffer']:
            ffmpeg_args = settings['settings']['default_ffmpeg_pipe_args']
            ffmpeg_args = ffmpeg_args.replace("[URL]", url)
            service_name = re.sub('[^a-zA-Z0-9 \n\.]', '', service_name)
            service_name = re.sub('\s', '-', service_name)
            ffmpeg_args = ffmpeg_args.replace("[SERVICE_NAME]", service_name.lower())
            url = f"pipe://ffmpeg {ffmpeg_args}"
    return url
