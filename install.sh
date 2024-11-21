#!/bin/bash

sudo mkdir /opt/compress2cord
sudo cp ./compress2cord.py /opt/compress2cord/compress2cord.py
sudo cp -r ./assets /opt/compress2cord/
sudo cp ./frame.py /opt/compress2cord/frame.py
sudo ln -s /opt/compress2cord/compress2cord.py /usr/local/bin/compress2cord
sudo chown root:root /usr/local/bin/compress2cord
sudo chmod +x /usr/local/bin/compress2cord
