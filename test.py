import sys
import time
import os
import json
import subprocess

def getCodecs():
    ffprobe_bin = "/usr/bin/ffprobe"
    command = [
        ffprobe_bin,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-encoders"
    ]
    
    allowed_audio_codecs = [
        'opus',
        'aac',
    ]
    
    allowed_video_codecs = [
        '264',
        '265','hevc',
        'av1',
        'vp9'
    ]
    
    codecs = {}
    video = []
    audio = []
    result = subprocess.run(command, capture_output=True, text=True)
    stdout = result.stdout.split("\n")
    for line in stdout:
        codec = line.strip().split()
        if len(codec) > 1:
            if "V" in codec[0] and any(sub in codec[1] for sub in allowed_video_codecs):
                video += [codec[1]]
            elif "A" in codec[0] and any(sub in codec[1] for sub in allowed_audio_codecs):
                audio += [codec[1]]
    video += ['vnull']
    audio += ['disabled']
    codecs['video'] = video
    codecs['audio'] = audio
    return codecs

codecs = getCodecs()
video = codecs['video']
audio = codecs['audio']
print(video, audio)
