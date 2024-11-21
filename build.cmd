python -m venv ./venv-windows
source ./venv-windows/Scripts/activate.bat
pyinstaller --name "compress2cord" --add-data "lib/ffmpeg.exe:lib" --add-data "lib/ffprobe.exe:lib" ./compress2cord
echo.
echo Build Done
echo.
dir ./dist/
