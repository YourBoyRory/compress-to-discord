#!/usr/bin/python
import subprocess
from fractions import Fraction
import argparse
import json
import sys
import os

NITRO_MB = (1000, '1GB')
NITRO_CLASSIC_MB = (50, '50MB')
DISCORD_MB = (20, '20MB')
OLD_MB = (8, '8MB')

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

    def checkLibraries(self, name=None):
        library = {
            'ffmpeg': {
                'bin': self.ffmpeg_bin,
                'exists': os.path.exists(self.ffmpeg_bin)
            },
            'ffprobe': {
                'bin': self.ffprobe_bin,
                'exists': os.path.exists(self.ffprobe_bin)
            }
        }
        if name != None:
            return library.get(name, {})
        else:
            return library

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
            raise Exception(f'{result.stderr}')
        meta_data = json.loads(result.stdout)
        meta_data_format = meta_data.get("format", {})
        meta_data_streams = meta_data.get("streams", {})
        meta_data_datastream = {}
        for stream in meta_data_streams:
            if stream.get('codec_type', None) == 'data':
                meta_data_datastream = stream
                data_keys = ['duration', 'bitrate', 'nb_frames', 'frame_rate']
                if all(
                    any(key in stream_key for stream_key in stream)
                    for key in data_keys
                ): break
        if meta_data_format == {} and meta_data_streams == {}:
            raise ValueError("Is this a video file?")
        meta_data_trimmed = {
            "duration": float(meta_data_format.get('duration', -1.0)),
            "bitrate": float(meta_data_format.get('bit_rate', -1.0)),
            "nb_frames": 0,
            "resolution": "Unknown",
            "framerate": 0.0,
            "filesize": float(meta_data_format.get('size', -1.0))
        }
        found_video_stream = False
        for stream in meta_data_streams:
            if stream.get('codec_type', None) == 'video':
                found_video_stream = True

                # Duration
                data_in = stream.get(
                    'duration',
                    meta_data_format.get(
                        'duration',
                        meta_data_datastream.get(
                            'duration',
                            -1.0
                        )
                    )
                )
                try:
                    meta_data_trimmed["duration"] = float(data_in)
                except Exception as e:
                    self.inform("WARN", f"Unexpected data for Duration: {data_in} ({e})", True)

                # Bitrate
                data_in = stream.get(
                    'bit_rate',
                    meta_data_format.get(
                        'bit_rate',
                        meta_data_datastream.get(
                            'bit_rate',
                            -1.0
                        )
                    )
                )
                try:
                    meta_data_trimmed["bitrate"] = float(data_in)
                except Exception as e:
                    self.inform("WARN", f"Unexpected data for Bitrate: {data_in} ({e})", True)

                # Framerate
                data_in = stream.get('r_frame_rate',
                    stream.get(
                        'avg_frame_rate',
                        meta_data_datastream.get(
                            'r_frame_rate',
                            meta_data_datastream.get(
                                'avg_frame_rate',
                                0.0
                            )
                        )
                    )
                )
                try:
                    if data_in == "0/0": data_in = 0.0
                    meta_data_trimmed["framerate"] = float(Fraction(data_in))
                except Exception as e:
                    self.inform("WARN", f"Unexpected data for Framerate: {data_in} ({e})", True)

                # Frame Count
                data_in = stream.get('nb_frames',
                    meta_data_datastream.get('nb_frames',
                        meta_data_trimmed["duration"] * meta_data_trimmed["framerate"]
                    )
                )
                try:
                    meta_data_trimmed["nb_frames"] = int(data_in)
                except Exception as e:
                    self.inform("WARN", f"Unexpected data for Frame Count: {data_in} ({e})", True)

                # Resolution
                data_in = stream.get('height', "Unknown")
                if data_in == "Unknown" or str(data_in).isdigit():
                    meta_data_trimmed["resolution"] = data_in
                else:
                    self.inform("WARN", f"Unexpected data for Resolution: {data_in} (Not a whole number)", True)

                break
        if not found_video_stream:
            raise ValueError("Is this a video file?")
        for key, value in meta_data_trimmed.items():
            if key in ['duration', 'bitrate', 'filesize'] and value == -1.0:
                raise ValueError(f"Failed to get video {key} from any provider.")
            elif key == 'framerate' and value == 0.0:
                self.inform("WARN", f"{file} Failed to get video framerate from any provider. Gussed 30fps and Continued.", True)
                meta_data_trimmed["framerate"] = 30.0
            elif key == 'nb_frames' and value == 0:
                self.inform("WARN", f"{file} Failed to get total frame count from any provider. Continued without progress monitor.", True)
            elif key == 'resolution' and value == "Unknown":
                self.inform("WARN", f"{file} Failed to get video resolution from any provider. Continued without reducing.", True)
        return meta_data_trimmed

    def getAudioBitrate(self, bitrate):
        target_audio_bitrate=[64000,56000,48000,32000,22000,16000,14000,12000,8000,6000,4000,2000]
        multiplyer=0.25
        audio_options = ["-an"]
        if self.options['audio_codec'] == "disabled":
            return audio_options, bitrate
        for rate in target_audio_bitrate:
            if rate < bitrate * multiplyer:
                self.inform("INFO", f"Target audio bitrate {rate}kbps")
                audio_options = ["-acodec", self.options['audio_codec'], "-b:a", str(rate)]
                bitrate -= rate
                break
        if audio_options[0] == "-an":
            #if all else fails go as low as possible allowing over head file size
            audio_options = ["-acodec", self.options['audio_codec'], "-ac", "1", "-b:a", "1000"]
        return audio_options, bitrate

    def getEncoderOptions(self):
        codec = self.options['video_codec']
        codec_options = ["-c:v", codec]
        profile_options = []
        speed_options = []
        pix_fmt_options = []
        if self.options['profile'] != "":
            profile = self.options['profile']
            profile_options = ["-profile:v", self.options['profile']]
            pix_fmt = "+yuv"
            if '444' in profile:
                pix_fmt+="444p10le"
            elif '422' in profile:
                pix_fmt+="422p10le"
            else:
                pix_fmt+="420p"
                if "10" in profile:
                    pix_fmt+="10le"
            if pix_fmt != "+yuv":
                pix_fmt_options = ['-pix_fmt', pix_fmt]
        if self.options['speed'] != "":
            speed_options = ["-preset", self.options['speed']]
        print(codec_options + profile_options + speed_options + pix_fmt_options)
        return codec_options + profile_options + speed_options + pix_fmt_options

    def getDecoderOptions(self, target_resolution):
        codec = self.options['video_codec']
        decode_options = []
        scale_param_base = f"=-2:{target_resolution}"
        scale_param = f"scale{scale_param_base}"
        hwaccels = ['vdpau', 'cuda', 'vaapi', 'qsv', 'drm', 'opencl', 'vulkan']
        hwaccel = next((hw for hw in hwaccels if hw in codec), None)
        if 'nvenc' in codec:
            decode_options = ['-hwaccel', 'cuda', "-hwaccel_output_format", 'cuda']
            scale_param = f"scale_cuda{scale_param_base}"
        if 'amf' in codec:
            decode_options = ['-hwaccel', 'amf', "-hwaccel_output_format", 'amf']
        elif hwaccel:
            decode_options = ['-hwaccel', hwaccel, "-hwaccel_output_format", hwaccel]
            if '10' in codec:
                pix_fmt = "p010le"
            else:
                pix_fmt = "nv12"
            scale_param = f"scale_{hwaccel}{scale_param_base}:format={pix_fmt}"
        return decode_options, scale_param

    def compressVideo(self, file, target_path=None, wait=True):
        size_bytes = self.options['file_size']
        ffmpeg_data = {}
        try:
            meta_data = self.getVideoInfo(file)
        except Exception as e:
            self.inform("ERROR", f"{file} Unsupported or corrupt file - codec metadata was not readable; {e}")
            self.videosFailed += 1
            return ffmpeg_data
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
        decode_options, scale_param = self.getDecoderOptions(target_resolution)
        encode_options = self.getEncoderOptions()
        command = [self.ffmpeg_bin, "-y"]
        command += decode_options
        command += [
            "-i", file,
            "-maxrate", str(target_bitrate),
            "-bufsize", str(target_bitrate)
        ]
        if not (target_bitrate >= meta_data["bitrate"]):
            self.inform("INFO", f"Targeting ~{int(size_bytes/1024/1024)}MB with {int(target_bitrate/1024)}kbps @ {target_resolution}p\n")
            compressed = True
            command += [
                "-b:v", str(target_bitrate),
                '-vf', scale_param
            ]
        else:
            compressed = False
            self.inform("INFO", f"{file} was already smaller then {int(size_bytes/1024/1024)}MB.")
        command += encode_options
        command += audio_options
        command += [target_path]
        try:
            result = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as e:
            self.inform("ERROR", f"{file} Could not compress; {e}")
            self.videosFailed += 1
            return ffmpeg_data

        ffmpeg_data = {
            'nb_frames': meta_data['nb_frames'],
            'codec': self.options['video_codec'],
            'compressed': compressed
        }

        if wait:
            result.wait()
            self.inform("INFO", f"Wrote {target_path}")
            if result.returncode == 0:
                self.videosCompessed += 1
            else:
                self.videosFailed += 1
            return ffmpeg_data
        else:
            ffmpeg_data['ffmpeg_pointer'] = result
            return ffmpeg_data

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

    def inform(self, msg_type, msg, quiet=False):
        if not quiet:
            if msg_type == "WARN" or msg_type == "ERROR":
                self.log+=f"{msg}\n"
        self.lastMessageType = msg_type
        self.lastMessage = msg
        print(f"{msg_type}: {msg}")


def showHelp():
    print("\nUSAGE:\n")
    print(f"    {sys.argv[0]} [Options] [VIDEO_PATH]\n\n")
    print("    -h; --help                 Show this help dialog.")
    print("    --custom [float|int]       Set a custom target file size.")
    print("                               if you still have access to the old larger file size limit.\n\n")
    print("PRESETS:\n")
    print("    --nitro                    Compresses within the Discord Nitro file size limit (1GB).")
    print("    --nitro-basic; --basic     Compresses within the Discord Nitro Basic file size limit (50MB).")
    print("    --old                      Compresses within the old file size limit (8MB).\n")

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Compress2Cord compresses a video to fit within "
            "a Discord attachment file size limit."
        ),
        epilog="If no VIDEO_PATH is provided, the GUI will launch."
    )

    size_group = parser.add_mutually_exclusive_group()

    size_group.add_argument(
        "--nitro",
        action="store_const",
        const= NITRO_MB[0] * 1024 * 1024,
        dest="size",
        help=f"Compress within the Discord Nitro file size limit ({NITRO_MB[1]})."
    )

    size_group.add_argument(
        "--nitro-basic",
        "--basic",
        action="store_const",
        const=NITRO_CLASSIC_MB[0] * 1024 * 1024,
        dest="size",
        help=f"Compress within the Discord Nitro Basic limit ({NITRO_CLASSIC_MB[1]})."
    )

    size_group.add_argument(
        "--old",
        action="store_const",
        const=OLD_MB[0] * 1024 * 1024,
        dest="size",
        help=f"Compress within the old file size limit ({OLD_MB[1]})."
    )

    size_group.add_argument(
        "--custom",
        type=float,
        metavar="MB",
        dest="custom_size",
        help="Set a custom target file size in MB."
    )

    parser.add_argument(
        "video_paths",
        nargs="*",
        metavar="VIDEO_PATH",
        help=f"One or more videos to compress to {DISCORD_MB[1]} (Default)."
    )

    args = parser.parse_args()

    # Default size: 20 MB
    if args.custom_size is not None:
        if args.custom_size <= 0:
            parser.error("--custom must be greater than 0")

        args.size = args.custom_size * 1024 * 1024
    elif args.size is None:
        args.size = DISCORD_MB[0] * 1024 * 1024

    return args


def venv_error(error):
    import tkinter as tk
    import traceback
    from tkinter import messagebox

    if os.name == 'nt':
        message = "Make sure the '_internal' folder privided with the download is updated and included in the same directory as the executable."
    else:
        message = "The python venv is corrupt or outdated. Please reinstall Compress2Cord."

    traceback.print_exc()
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"{error}\n\n{message}")
    root.destroy()

if __name__ == "__main__":
    args = parse_args()

    if args.video_paths:
        compressor = VideoCompressor({
                'file_size': args.size,
                'video_codec': 'libx264',
                'speed': 'slow',
                'profile': 'high',
                'audio_codec': 'acc'
            }
        )
        for video_path in args.video_paths:
            file = os.path.abspath(video_path)
            compressor.compressVideo(file)
    else:
        try:
            sys.path.append("/opt/compress2cord")
            from frame import SpawnFrame
            SpawnFrame()
        except ModuleNotFoundError as e:
            venv_error(e)
        except ImportError as e:
            venv_error(e)

