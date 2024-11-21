#!/usr/bin/python

import subprocess
import json
import sys
import os

class VideoCompressor:

    def __init__(self, target_size_bytes, profile='slow', video_codec='libx264', audio_codec='aac'):
        if os.name == 'nt':
            self.ffmpeg_bin = self.getAssetPath("ffmpeg.exe")
            self.ffprobe_bin = self.getAssetPath("ffprobe.exe")
        else:
            self.ffmpeg_bin = "/usr/bin/ffmpeg"
            self.ffprobe_bin = "/usr/bin/ffprobe"
        print(self.ffmpeg_bin)
        print(self.ffprobe_bin)
        self.lastMessageType=""
        self.lastMessage=""
        self.log=""
        self.lastPath=""
        self.options = {
            'target_size_bytes': target_size_bytes,
            'profile': profile,
            'video_codec': video_codec,
            'audio_codec': audio_codec
        }

    def getAssetPath(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'lib', file)

    def getTargetResolution(self, target_bitrate, resolution, framerate):
        bitrate_multiplyer = framerate/30
        bitrate = target_bitrate/bitrate_multiplyer
        bitrate_mapping = {
            "2160": 8000000,
            "1440": 3500000,
            "1080": 2000000,
            "720": 1000000,
            "480": 500000,
            "360": 0
        }
        for res, bit in bitrate_mapping.items():
            if bitrate >= bit:
                return res

    def getVideoInfo(self, file):
        meta_data_trimmed = {}
        command = [
            self.ffprobe_bin,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.stderr:
            self.inform("Error:", result.stderr)
            raise
        meta_data = json.loads(result.stdout)
        for steam in meta_data['streams']:
            try:
                meta_data_trimmed["duration"] = float(steam['duration'])
                meta_data_trimmed["bitrate"] = float(steam['bit_rate'])
                meta_data_trimmed["resolution"] = steam['height']
                meta_data_trimmed["framerate"] = eval(steam['r_frame_rate'])
            except:
                meta_data_trimmed = {}
            if meta_data_trimmed != {}:
                break
        if meta_data_trimmed == {}:
            meta_data_trimmed["duration"] = float(meta_data['format']['duration'])
            meta_data_trimmed["bitrate"] = float(meta_data['format']['bit_rate'])
            meta_data_trimmed["resolution"] = "Unknown"
            meta_data_trimmed["framerate"] = 30
        meta_data_trimmed["filesize"] = float(meta_data['format']['size'])
        return meta_data_trimmed

    def getAudioBitrate(self, bitrate):
        target_audio_bitrate=[64000,56000,48000,32000,22000]
        multiplyer=0.25
        audio_options = ["-an"]
        for rate in target_audio_bitrate:
            if rate < bitrate * multiplyer:
                self.inform("INFO:", f"Target audio bitrate {rate}kbps")
                audio_options = ["-acodec", self.options['audio_codec'], "-b:a", str(rate)]
                bitrate -= rate
                break
        #audio_options = ["-acodec", self.options['audio_codec'], "-b:a", "48000"]
        if audio_options[0] == "-an":
            self.inform("WARN", "File too big. Audio disabled.")
        return audio_options, bitrate


    def compressVideo(self, file, isGui=0):
        size_bytes = self.options['target_size_bytes']
        #try:
        meta_data = self.getVideoInfo(file)
        #except:
        #    print("ERROR: Video Meta data is not readable")
        #    exit()
        file_size = int(meta_data['filesize']/1024/1024)
        file_bitrate = meta_data['bitrate']
        file_resolution = meta_data['resolution']
        if isGui:
            os.makedirs(os.path.expanduser('~/Videos/compess2cord/'), exist_ok=True)
            target_path = os.path.join(os.path.expanduser('~/Videos/compess2cord/'), os.path.splitext(os.path.basename(file))[0] + ".compressed.mp4")
        else:
            target_path = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0] + ".compressed.mp4")
        target_size = size_bytes * 8
        target_bitrate = int((target_size/meta_data["duration"]))
        target_resolution = self.getTargetResolution(target_bitrate, file_resolution, meta_data["framerate"])
        self.inform("\nINFO", f"Input file {file_size}MB with {int(file_bitrate/1024)}kbps @ {file_resolution}p")
        audio_options, target_bitrate = self.getAudioBitrate(target_bitrate)
        command = [
            self.ffmpeg_bin,
            "-y",
            "-i", file,
            "-c:v", self.options['video_codec'],
            "-b:v", str(target_bitrate),
            "-maxrate", str(target_bitrate),
            "-bufsize", str(target_bitrate),
            '-vf', f"scale=-2:{target_resolution}",
            "-preset", self.options['profile']
        ]
        command += audio_options
        command += [target_path]
        if not (target_bitrate >= meta_data["bitrate"]):
            self.inform("INFO", f"Targeting ~{int(size_bytes/1024/1024)}MB with {int(target_bitrate/1024)}kbps @ {target_resolution}p\n")
            #if (target_bitrate > 18000):
            subprocess.run(command)
            #else:
            #    print(f"ERROR: {file} is too big to be compressed to {int(size_bytes/1024/1024)}MB. Skipping...")
            self.inform("INFO", f"Wrote {target_path}")
        else:
            self.inform("WARN", f"{file} is small enough. Skipping...")
        self.lastPath = os.path.dirname(target_path)

    def clearLog(self):
        self.log=""

    def inform(self, msg_type, msg):
        if msg_type == "WARN" or msg_type == "ERROR":
            self.log+=f"{msg}\n"
        self.lastMessageType = msg_type
        self.lastMessage = msg
        print(f"{msg_type}: {msg}")


def showHelp():
    print("\nUSAGE:\n")
    print(f"    {sys.argv[0]} [Options] [VIDEO_PATH]\n\n")
    print("    -h; --help                 Show this help dialog.")
    print("    --custom [float|int]       Set the target file size. You can set this to \"25\"")
    print("                               if you still have access to the old larger file size limit.\n\n")
    print("PRESETS:\n")
    print("    --nitro                    Compresses within the Discord Nitro file size limit (500MB).")
    print("    --nitro-basic; --basic     Compresses within the Discord Nitro Basic file size limit (50MB).")
    print("    --old                      Compresses within the old file size limit (8MB).\n")

if __name__ == '__main__':
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\n    Compress2Cord is a python script that will compress a video to fit as an attachment")
        print("    on Discord. By default, this script will compress a provided video at 10MB, but")
        print("    this can be customized.\n")
        showHelp()
        exit()
    elif "--nitro-basic" in sys.argv or "--basic" in sys.argv:
        SIZE = 50 * 1024 * 1024
    elif "--nitro" in sys.argv:
        SIZE = 500 * 1024 * 1024
    elif "--custom" in sys.argv:
        i = sys.argv.index("--custom")+1
        SIZE = float(sys.argv[i]) * 1024 * 1024
    elif "--old" in sys.argv:
        SIZE = 8 * 1024 * 1024
    else:
        SIZE = 10 * 1024 * 1024

    if len(sys.argv) > 1:
        compressor = VideoCompressor(SIZE, "fast", "libx264", "aac")
        compressor.compressVideo(os.path.abspath(sys.argv[-1]))
    else:
        print("\nERROR: Incorrect Syntax")
        showHelp()
