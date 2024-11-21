python -m venv ./venv-windows
source ./venv-windows/Scripts/activate.bat
pip install -r requirements-windows.txt
pyinstaller --name "compress2cord" --add-data "assets/ggsans.ttf:assets" --add-data "assets/loading.gif:assets" --add-data "lib/ffmpeg.exe:lib" --add-data "lib/ffprobe.exe:lib" ./frame.py
