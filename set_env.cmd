python -m venv ./venv-windows
source ./venv-windows/Scripts/activate.bat
pip install -r requirements-windows.txt
pyinstaller --windowed --name "Compress2Cord" --icon=assets/icon.ico --add-data "assets/file.png:assets" --add-data "assets/arrow.png:assets" --add-data "assets/settings.png:assets" --add-data "assets/icon.png:assets" --add-data "assets/ggsans.ttf:assets" --add-data "assets/loading.gif:assets" --add-data "lib/ffmpeg.exe:lib" --add-data "lib/ffprobe.exe:lib" ./frame.py
