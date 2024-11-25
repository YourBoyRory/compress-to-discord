#!/usr/bin/python
import subprocess
import json
import sys
import os

class VideoCompressor:

    def __init__(self, options=None):
        if os.name == 'nt':
            self.ffmpeg_bin = self.getAssetPath("ffmpeg.exe")
            self.ffprobe_bin = self.getAssetPath("ffprobe.exe")
        else:
            self.ffmpeg_bin = "/usr/bin/ffmpeg"
            self.ffprobe_bin = "/usr/bin/ffprobe"
        print(self.ffmpeg_bin)
        print(self.ffprobe_bin)
        self.videosCompessed = 0
        self.videosFailed = 0
        self.videosSkipped = 0
        self.log = ""
        if options == None:
            self.options = {
                'file_size': 10 * 1024 * 1024,
                'video_codec': 'libx264',
                'speed': 'slow',
                'profile': 'high',
                'audio_codec': 'libopus'
            }
        else:
            self.options = options
        
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
        target_audio_bitrate=[64000,56000,48000,32000,22000,16000,14000,12000,8000,6000,4000,2000]
        multiplyer=0.25
        audio_options = ["-an"]
        if self.options['audio_codec'] == "disabled":
            return audio_options, bitrate
        for rate in target_audio_bitrate:
            if rate < bitrate * multiplyer:
                self.inform("INFO:", f"Target audio bitrate {rate}kbps")
                audio_options = ["-acodec", self.options['audio_codec'], "-b:a", str(rate)]
                bitrate -= rate
                break
        if audio_options[0] == "-an":
            #if all else fails go as low as possible allowing over head file size
            audio_options = ["-acodec", self.options['audio_codec'], "-ac", "1", "-b:a", "1000"]
        return audio_options, bitrate

    def getVideoOptions(self):
        codec = ["-c:v", self.options['video_codec']]
        profile = []
        speed = []
        if self.options['profile'] != "":
            profile = ["-profile:v", self.options['profile']]
        if self.options['speed'] != "":
            speed = ["-preset", self.options['speed']]
        print(self.options['profile'], self.options['speed'])
        print(codec + profile + speed)
        return codec + profile + speed
        
    def compressVideo(self, file, target_path=None):
        size_bytes = self.options['file_size']
        try:
            meta_data = self.getVideoInfo(file)
        except:
            self.inform("ERROR", f"{file} Codec metadata was not readable")
            self.videosFailed += 1
            return
        file_size = int(meta_data['filesize']/1024/1024)
        file_bitrate = meta_data['bitrate']
        file_resolution = meta_data['resolution']
        if target_path == None:
            target_path = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0] + ".compressed.mp4")
        target_size = size_bytes * 8
        target_bitrate = int((target_size/meta_data["duration"]))
        target_resolution = self.getTargetResolution(target_bitrate, file_resolution, meta_data["framerate"])
        self.inform("\nINFO", f"Input file {file_size}MB with {int(file_bitrate/1024)}kbps @ {file_resolution}p")
        audio_options, target_bitrate = self.getAudioBitrate(target_bitrate)
        video_options = self.getVideoOptions()
        command = [
            self.ffmpeg_bin,
            "-y",
            "-i", file,
            "-b:v", str(target_bitrate),
            "-maxrate", str(target_bitrate),
            "-bufsize", str(target_bitrate),
            '-vf', f"scale=-2:{target_resolution}",
        ]
        command += video_options
        command += audio_options
        command += [target_path]
        if not (target_bitrate >= meta_data["bitrate"]):
            self.inform("INFO", f"Targeting ~{int(size_bytes/1024/1024)}MB with {int(target_bitrate/1024)}kbps @ {target_resolution}p\n")
            #if (target_bitrate > 18000):
            result = subprocess.run(command) 
            #result = subprocess.run(command, capture_output=True) 
            #else:
            #    print(f"ERROR: {file} is too big to be compressed to {int(size_bytes/1024/1024)}MB. Skipping...")
            self.inform("INFO", f"Wrote {target_path}")
            if result.returncode == 0:
                self.videosCompessed += 1
            else:
                self.videosFailed += 1
        else:
            self.inform("WARN", f"{file} was already smaller then {int(size_bytes/1024/1024)}MB.")
            self.videosSkipped += 1

    def getCodecs(self):
        command = [
            self.ffprobe_bin,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-encoders"
        ]
        
        allowed_audio_codecs = [
            'libopus',
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

    def clearLog(self):
        self.videosCompessed = 0
        self.videosFailed = 0
        self.videosSkipped = 0
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
        compressor = VideoCompressor(SIZE, "fast", "high", "libx264", "libopus")
        file = os.path.abspath(sys.argv[-1])
        compressor.compressVideo(file)
    else:
        sys.path.append('/opt/compress2cord')
        from frame import SpawnFrame
        SpawnFrame()
        exit()

