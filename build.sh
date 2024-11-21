#!/bin/bash

if mkdir ./lib; then
    wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
    unzip -j ./ffmpeg-master-latest-win64-gpl.zip ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe -d ./lib/
    unzip -j ./ffmpeg-master-latest-win64-gpl.zip ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe -d ./lib/
    rm ./ffmpeg-master-latest-win64-gpl.zip
fi
wine ./set_env.cmd
ls -l ./dist/compress2cord
