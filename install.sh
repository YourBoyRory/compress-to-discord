#!/bin/bash

# install app

sudo mkdir /opt/compress2cord
sudo cp ./compress2cord.py /opt/compress2cord/compress2cord.py
sudo cp -r ./assets /opt/compress2cord/
sudo cp ./frame.py /opt/compress2cord/frame.py
sudo ln -s /opt/compress2cord/compress2cord.py /usr/local/bin/compress2cord
sudo chown root:root /usr/local/bin/compress2cord
sudo chmod +x /usr/local/bin/compress2cord

sudo tee /usr/share/applications/compress2cord.desktop > /dev/null <<EOF
[Desktop Entry]
Version=1.0
Name=Compress2Cord
Comment=Compress any video to fit on discord
Exec=/usr/bin/python /opt/compress2cord/frame.py
Icon=/opt/compress2cord/assets/icon.png
Terminal=false
Type=Application
Categories=Multimedia;Video;Utility;AudioVideo;
EOF
