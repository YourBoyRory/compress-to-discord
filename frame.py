import sys
import time
import os
import json
import re
import subprocess
import threading
from compress2cord import VideoCompressor
from PyQt5.QtCore import Qt, QThread, QSize,  pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDoubleValidator, QDropEvent, QMovie, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import QFrame, QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox, QPushButton, QDialog, QComboBox, QLineEdit, QSpacerItem, QSizePolicy

NITRO_MB = (1000, 'Nitro (1GB)')
NITRO_CLASSIC_MB = (50, 'Nitro Basic (50MB)')
DISCORD_MB = (20, 'Discord (20MB)')
CUSTOM_MB = (DISCORD_MB[0], 'Custom')

def venv_error(error):
    import tkinter as tk
    from tkinter import messagebox

    if os.name == 'nt':
        message = "Make sure the '_internal' folder privided with the download is updated and included in the same directory as the executable."
    else:
        message = "The python venv is corrupt or outdated. Please reinstall Compress2Cord."
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"{error}\n\n{message}")
    root.destroy()

class StyleSheets():
    def getAssetPath(file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, 'assets', file)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"{full_path} not found.")
        return full_path

    try:
        image = getAssetPath("arrow.png")
    except FileNotFoundError as e:
        image = "arrow.png"

    options_stylesheet = (f"""
        QWidget {{
            background-color: #313338;
            color: white;
            font-size: 16px;
        }}
        QLabel {{
            color: #b5bac1;
            font-weight: bold;
            font-size: 12px;
        }}
        QFrame {{
            background-color: #313338;
            border: 0px solid #313338;
            padding: 0;
        }}
        QComboBox {{
            background-color: #1e1f22;
            border: 5px solid #1e1f22;
            border-radius: 5px;
            padding: 5;
            font-size: 14px;
            color: white;
        }}
        QLineEdit {{
            background: #1e1f22;
            font-size: 14px;
            color: white;
        }}
        QPushButton {{
            background-color: #5865f2;
            border: 5px solid #5865f2;
            border-radius: 5px;
            padding: 2;
            color: white;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: #4752c4;
            border: 8px solid #4752c4;
            border-radius: 5px;
        }}
        QPushButton:pressed {{
            background-color: #3c45a5;
            border: 8px solid #3c45a5;
            border-radius: 5px;
        }}
        QComboBox::down-arrow {{
            image: url({image});
            width: 14px;
            height: 13px;
        }}
        QComboBox:drop-down {{
            border: none;
            background-color: transparent;
        }}
    """)

    main_stylesheet = ("""
        QWidget {
            background-color: #2b2d31;
            color: white;
            font-size: 16px;
        }
        QLabel {
            color: #f2f3e9;
            font-size: 12px;
        }
        QFrame {
            background-color: #313338;
            border: 5px solid #313338;
            border-radius: 8px;
            padding: 10;
        }
        QPushButton {
            background-color: #5865f2;
            border: 5px solid #5865f2;
            border-radius: 5px;
            padding: 2;
            padding-left: 20px;
            padding-right: 20px;
            color: white;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #4752c4;
            border: 8px solid #4752c4;
            border-radius: 5px;
        }
        QPushButton:pressed {
            background-color: #3c45a5;
            border: 8px solid #3c45a5;
            border-radius: 5px;
        }
    """)


class Compess(QThread):
    # A signal to send the result back to the main thread
    finished = pyqtSignal(str, int, int, int)

    def __init__(self, window, options):
        super().__init__()
        self._stop_event = threading.Event()
        self._skip_event = threading.Event()
        self.SIZE = int(float(options["file_size"])/1024/1024)
        self.compressor = VideoCompressor(options)
        self.window = window

    def getCodecs(self):
        return self.compressor.getCodecs()

    def setBatch(self, urls):
        self.urls = urls

    def setOptions(self, options):
        self.SIZE = int(float(options["file_size"])/1024/1024)
        self.compressor = VideoCompressor(options)

    def run(self):
        count=1
        self._skip_event.clear()
        for file in self.urls:
            error_message = "Error while opening encoder - Might be a unsupported file or have a impossible filesize, codecs, or profile set."
            input_file = os.path.abspath(file.toLocalFile())
            file_name = os.path.basename(input_file)
            file_name = file_name[:50] + "..." if len(file_name) > 10 else file_name
            self.window.label.setText(f"{file_name}\n")
            os.makedirs(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord"), exist_ok=True)
            output_file = str(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord", os.path.splitext(os.path.basename(input_file))[0] + ".compressed.mp4"))
            ffmpeg_data = self.compressor.compressVideo(input_file, output_file, False)
            process = ffmpeg_data.get('ffmpeg_pointer', None)
            frame_count = ffmpeg_data.get('nb_frames', None)
            compressed = ffmpeg_data.get('compressed', None)
            codec = ffmpeg_data.get('codec', None)
            if compressed:
                bottom_text = f"[{count}/{len(self.urls)}] Compressing to {self.SIZE}MB..."
            else:
                bottom_text = f"[{count}/{len(self.urls)}] Re-encoding to {codec}..."
            self.window.show_folder_btn.setIconSize(QSize(0, 0))
            self.window.show_folder_btn.setText(bottom_text)
            if process:
                last_time_sec = None
                for line in process.stdout:
                    if self._stop_event.is_set():
                        process.kill()
                        return
                    if self._skip_event.is_set():
                        process.kill()
                        self.compressor.inform("WARN", f"{input_file} was skipped by user.")
                        self.compressor.videosSkipped += 1
                        break
                    print(line, end="")
                    for helpful_error_match in ['[error]','Cannot load', "Impossible to convert", "failed to open", "No device available"]:
                        if helpful_error_match in line:
                            error_message = line
                    match = re.search(r'frame=\s*(\d+)\s+fps=\s*(\d+)', line)
                    if match and frame_count > 0:
                        frame=int(match.group(1))
                        fps=int(match.group(2))
                        percent = int((frame/frame_count)*100)
                        if fps > 0:
                            time_sec = (frame_count-frame)//max(fps,1)
                            if last_time_sec == None:
                                last_time_sec = time_sec+1
                            if last_time_sec > time_sec:
                                if time_sec >= 55:
                                    time = f"{round(time_sec / 60)} minutes remain"
                                elif time_sec <= 1:
                                    time = f"1 second remain"
                                elif time_sec < 10:
                                    time = f"{time_sec} seconds remain"
                                else:
                                    time = f"{round(time_sec / 10) * 10} seconds remain"
                                self.window.label.setText(f"{file_name}\n{time} - {percent}%")
                                last_time_sec = time_sec
                if frame_count > 0:
                    self.window.label.setText("0 seconds remain - 100%")
                process.wait()
                count+=1
                if self._skip_event.is_set():
                    self._skip_event.clear()
                elif process.returncode == 0:
                    self.compressor.videosCompessed += 1
                else:
                    self.compressor.videosFailed += 1
                    self.compressor.inform("ERROR", f"{input_file} {error_message}")


        self.finished.emit(self.compressor.log, self.compressor.videosCompessed, self.compressor.videosFailed, self.compressor.videosSkipped)
        self.compressor.clearLog()

    def skip(self):
        print("Skipping...")
        self._skip_event.set()

    def stop(self):
        self._stop_event.set()
        self.wait()

class SetOptions(QDialog):
    def __init__(self, parent=None, options=None, codecs=None, open_count=1):
        super().__init__(parent)

        self.save = False
        self.open_count = open_count
        self.options = options
        self.codecs = codecs
        stylesheets = StyleSheets()
        self.setStyleSheet(stylesheets.options_stylesheet)

        self.setMinimumWidth(300)
        self.resize(400, 300)
        self.setWindowTitle('Options')

        # Create layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(48, 24, 48, 24)

        title = QLabel('Compression Settings')
        title.setStyleSheet("""
            QLabel {
                color: #f2f3f5;
                font-weight: normal;
                font-size: 16px;
            }
        """)
        layout.addWidget(title)

        #self.preset.addItems(["fast", "medium", "slow"])
        #self.profile.addItems(["baseline", "main", "high"])

        # File Size
        self.file_size_option, self.file_size_label = self.makeOption('file_size')
        self.custSizeField = QLineEdit(self)
        self.custSizeField.setPlaceholderText("Custom File Size (MB)")
        self.custSizeField.setValidator(QDoubleValidator(self))
        self.custSizeField.setHidden(True)
        self.file_size_option.currentTextChanged.connect(self.sizeChange)
        size = self.options['file_size']
        if size == NITRO_MB[0] * 1024 * 1024:
            size_option = NITRO_MB[1]
        elif size == NITRO_CLASSIC_MB[0] * 1024 * 1024:
            size_option = NITRO_CLASSIC_MB[1]
        elif size == DISCORD_MB[0] * 1024 * 1024:
            size_option = DISCORD_MB[1]
        else:
            self.custSizeField.setText(str(size/1024/1024))
            self.custSizeField.setHidden(False)
            size_option = CUSTOM_MB[1]
        self.file_size_option.setCurrentText(size_option)
        layout.addWidget(self.file_size_label)
        layout.addWidget(self.file_size_option)
        layout.addWidget(self.custSizeField)
        layout.addItem(QSpacerItem(0, 8))

        # Audio Codec
        self.audio_codec_option, self.audio_codec_label = self.makeOption('audio_codec')
        layout.addWidget(self.audio_codec_label)
        layout.addWidget(self.audio_codec_option)
        layout.addItem(QSpacerItem(0, 8))

        # Video Codec
        self.video_codec_option, self.video_codec_label = self.makeOption('video_codec')
        self.video_codec_option.currentTextChanged.connect(self.v_codecChange)
        layout.addWidget(self.video_codec_label)
        layout.addWidget(self.video_codec_option)
        layout.addItem(QSpacerItem(0, 8))

        self.profile_option, self.profile_label = self.makeOption('profile')
        layout.addWidget(self.profile_label)
        layout.addWidget(self.profile_option)
        layout.addItem(QSpacerItem(0, 8))

        self.speed_option, self.speed_label = self.makeOption('speed')
        layout.addWidget(self.speed_label)
        layout.addWidget(self.speed_option)
        layout.addItem(QSpacerItem(0, 8))

        # Add a button to submit the choices
        submit_button = QPushButton('Save')
        submit_button.clicked.connect(self.submit)
        submit_button.setMaximumWidth(90)
        layout.addWidget(submit_button, Qt.AlignCenter)

        self.v_codecChange(self.video_codec_option.currentText())

        layout.addStretch()

        # Set the layout for the dialog
        self.setLayout(layout)

    def makeOption(self, name):
        comboBox = QComboBox()
        lable = QLabel(name.upper().replace("_", " "))
        comboBox.addItems(self.getItems(name, comboBox))
        print(self.options, name)
        comboBox.setCurrentText(str(self.options[name]))
        return comboBox, lable

    def getItems(self, name, comboBox):
        match name:
            case "file_size":
                return [NITRO_MB[1], NITRO_CLASSIC_MB[1],  DISCORD_MB[1], CUSTOM_MB[1]]
            case "video_codec":
                return self.codecs['video']
            case "audio_codec":
                return self.codecs['audio']
            case _:
                return []


    def sizeChange(self, text):
        if text == "Custom":
            self.custSizeField.setHidden(False)
        else:
            self.custSizeField.setHidden(True)

    def getFilePath(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, 'etc', file)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"{full_path} not found.")
        return full_path

    def v_codecChange(self, text):

        try:
            with open(self.getFilePath("known_codecs.json")) as f:
                known_codecs = json.load(f)
        except FileNotFoundError as e:
            if self.open_count < 1:
                venv_error(e)
            known_codecs = {}
        except:
            known_codecs = {}

        if text in known_codecs:
            self.setCodecSettings(known_codecs[text].get('profiles',[]), known_codecs[text].get('preset',[]))
        elif any(sub in text for sub in ['264','265','hevc']):
            self.setCodecSettings(["baseline", "main", "high", "high10", "high422", "high444"],["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"])
        elif "av1" in text:
            self.setCodecSettings(None,["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"])
        elif "vp9" in text:
            self.setCodecSettings(None,["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"])
        elif text == "vnull":
            self.setCodecSettings(None, None)
        else:
            self.setCodecSettings(None, None)

    def setCodecSettings(self, profiles=[], speeds=[]):
        self.speed_option.clear()
        self.profile_option.clear()
        if profiles == [] or profiles == None:
            self.profile_label.setHidden(True)
            self.profile_option.setHidden(True)
            self.profile_option.addItems([])
        else:
            self.profile_label.setHidden(False)
            self.profile_option.setHidden(False)
            self.profile_option.addItems(profiles)
        if speeds == [] or profiles == None:
            self.speed_label.setHidden(True)
            self.speed_option.setHidden(True)
            self.speed_option.addItems([])
        else:
            self.speed_label.setHidden(False)
            self.speed_option.setHidden(False)
            self.speed_option.addItems(speeds)
        self.profile_option.setCurrentText(str(self.options['profile']))
        self.speed_option.setCurrentText(str(self.options['speed']))



    def submit(self):
        # Handle submission of selections
        choice_preset = self.speed_option.currentText()
        choice_profile = self.profile_option.currentText()
        choice_v_codec = self.video_codec_option.currentText()
        choice_a_codec = self.audio_codec_option.currentText()
        choice_size = self.file_size_option.currentText()

        if choice_size == NITRO_MB[1]:
            SIZE = NITRO_MB[0] * 1024 * 1024
        elif choice_size == NITRO_CLASSIC_MB[1]:
            SIZE = NITRO_CLASSIC_MB[0] * 1024 * 1024
        elif choice_size == CUSTOM_MB[1]:
            val = self.custSizeField.text()
            if val != "":
                SIZE = float(val) * 1024 * 1024
                print(float(val), SIZE)
            else:
                print(f"Defaulting to {CUSTOM_MB[0]}mb")
                SIZE = CUSTOM_MB[0] * 1024 * 1024
        else:
            SIZE = DISCORD_MB[0] * 1024 * 1024

        self.options['file_size'] =  SIZE
        self.options['speed'] = choice_preset
        self.options['profile'] = choice_profile
        self.options['video_codec'] = choice_v_codec
        self.options['audio_codec'] = choice_a_codec
        self.save = True
        self.accept()  # Close the dialog when done

class DragDropWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set the main window properties
        self.setWindowTitle("Compress2Cord")
        self.options_open_counter = 0
        load_errors = ""
        try:
            self.setWindowIcon(QIcon(self.getAssetPath('icon.png')))
        except FileNotFoundError as e:
            load_errors+= f"{e}\n"
        self.setGeometry(100, 100, 400, 300)
        self.setFixedSize(600, 400)
        self.setAcceptDrops(True)  # Enable drag-and-drop

        try:
            font_id = QFontDatabase.addApplicationFont(self.getAssetPath("ggsans.ttf"))
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            custom_font = QFont(font_family)
            self.setFont(custom_font)
        except FileNotFoundError as e:
            load_errors+= f"{e}\n"

        self.stylesheets = StyleSheets()
        try:
            # Check that this filed loaded in that class
            self.getAssetPath("arrow.png")
        except FileNotFoundError as e:
            load_errors+= f"{e}\n"
        self.setStyleSheet(self.stylesheets.main_stylesheet)

        # Add a label to display the instruction
        self.label = QLabel("Drag and drop your videos here", self)
        self.label.setStyleSheet("font-size: 16px; color: white;")
        self.label.setAlignment(Qt.AlignCenter)

        # Add a QLabel for the loading animation
        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignCenter)

        # Set up the loading animation (spinning wheel)
        try:
            self.movie = QMovie(self.getAssetPath("loading.gif"))  # Replace with path to your loading GIF
            self.loading_label.setMovie(self.movie)
        except FileNotFoundError as e:
            load_errors+= f"{e}\n"

        self.show_options_btn = QPushButton("")
        try:
            self.show_options_btn.setIcon(QIcon(self.getAssetPath('settings.png')))
        except FileNotFoundError as e:
            load_errors+= f"{e}\n"


        self.show_options_btn.setFixedSize(35,35)
        self.show_options_btn.setIconSize(QSize(21, 21))
        self.show_options_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: gray;

            }
        """)
        self.show_options_btn.clicked.connect(self.showOptionsWindow)

        self.show_folder_btn = QPushButton(" Show Output Folder  ")
        try:
            self.show_folder_btn.setIcon(QIcon(self.getAssetPath('file.png')))
        except FileNotFoundError as e:
            load_errors+= f"{e}\n"
        self.show_folder_btn.setIconSize(QSize(21, 21))
        self.show_folder_btn.setFixedHeight(35)
        self.show_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #949ba4;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #dbdee1;
            }
        """)
        self.show_folder_btn.clicked.connect(self.showFolder)

        # Layout to hold the labels
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 5, 20, 8)
        layout.addWidget(self.show_options_btn,Qt.AlignLeft)
        layout.addWidget(self.loading_label,Qt.AlignCenter)
        layout.addWidget(self.label,Qt.AlignCenter)
        layout.addWidget(self.show_folder_btn,Qt.AlignCenter)
        self.setLayout(layout)

        # Hide the loading label initially
        self.loadOptions()
        self.worker = Compess(self, self.options)
        self.worker.finished.connect(self.on_loading_complete)
        self.loading_label.setVisible(False)
        QTimer.singleShot(2000, self.checkLibraries)
        if load_errors != "":
            venv_error(load_errors)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.worker.skip()
        else:
            super().keyPressEvent(event)

    def checkLibraries(self):
        libraries = self.worker.compressor.checkLibraries()
        output = ""
        for key, value in libraries.items():
            if not value['exists']:
                lib_name = key
                lib_path = value['bin']
                output+=f"Missing '{lib_name}' Library:\n        path'{lib_path}' not found.\n\n"
        if output != "":
            if os.name == 'nt':
                output+="Make sure the '_internal' folder privided with the download is updated and included in the same directory as the executable."
            else:
                output+="\nPlease install or update ffmpeg from your package manager.\n"
            self.make_popup_window(None, "Libraries Missing", output, "").exec()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Called when a drag enters the widget"""
        if event.mimeData().hasUrls():  # Check if the drag contains files
            event.acceptProposedAction()  # Accept the event

    def dropEvent(self, event: QDropEvent):
        """Called when a file is dropped onto the widget"""
        # Get the file URL(s) that were dropped
        urls = event.mimeData().urls()

        if urls:
            if self.worker.isRunning():
                print("Thread: Locked")
                return
            file_path = urls[0].toLocalFile()

             # Show loading animation
            self.loading_label.setVisible(True)  # Show the loading spinner
            self.show_folder_btn.setEnabled(False)
            #self.show_folder_btn.setIconSize(QSize(0, 0))
            #self.label.setVisible(False)
            self.movie.start()  # Start the loading animation
            self.setStyleSheet(self.stylesheets.main_stylesheet)
            self.worker.setBatch(urls)
            self.worker.start()

            #self.worker = threading.Thread(target=self.compress, args=(urls,))
            #self.worker.start()

    def showFolder(self):
        path = os.path.join(os.path.expanduser("~"), "Videos", "compess2cord")
        try:
            if os.name == 'nt':
                # Use explorer to open the folder
                subprocess.run(["explorer", path])
            else:
                # Use the default file manager (e.g., nautilus, thunar, dolphin, etc.)
                subprocess.run(["xdg-open", path])
        except:
            print(f"ERROR: subprocess didn't work {os.name}, {path}")

    def showOptionsWindow(self):
        options_window = SetOptions(self, self.options, self.worker.getCodecs(), self.options_open_counter)
        options_window.exec_()
        self.options_open_counter+=1
        if options_window.save == True:
            self.writeOptions()
            self.worker.setOptions(self.options)


    def writeOptions(self):
        os.makedirs(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord"), exist_ok=True)
        with open(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord", ".compess2cord.json"), 'w') as f:
            json.dump(self.options, f)

    def loadOptions(self):
        os.makedirs(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord"), exist_ok=True)
        try:
            with open(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord", ".compess2cord.json")) as f:
                self.options = json.load(f)
        except:
            self.options = {
                'file_size': 10 * 1024 * 1024,
                'speed': 'slow',
                'profile': 'high',
                'video_codec': 'libx264',
                'audio_codec': 'libopus'
            }

    def on_loading_complete(self, log, videosCompessed, videosFailed, videosSkipped):
        self.movie.stop()  # Stop the loading animation
        self.setStyleSheet(self.stylesheets.main_stylesheet)
        self.setStyleSheet(self.stylesheets.main_stylesheet)
        self.loading_label.setVisible(False)  # Hide the loading spinner
        self.show_folder_btn.setEnabled(True)
        self.show_folder_btn.setIconSize(QSize(21, 21))
        #self.label.setVisible(True)
        self.label.setStyleSheet("font-size: 16px; color: white;")
        msg = self.make_popup_window(None, "Report", log, "")
        self.show_folder_btn.setText(" Show Output Folder  ")
        if videosFailed > 0:
            self.label.setText(f"One or more videos failed to compress to the target size\nCheck compession settings and try again\n\nDrag and drop more videos here")
        elif videosSkipped > 0 and videosCompessed == 0:
            self.label.setText(f"Drag and drop more videos here")
        else:
            self.label.setText(f"Videos Compessed\nDrag and drop more videos here")
        if log != "":
            msg.exec()

    def make_popup_window(self, mtype, title, top_text, bottom_text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        if mtype is not None:
            msg.setIcon(mtype)
        msg.setText(top_text)
        msg.setInformativeText(bottom_text)
        msg.setStyleSheet("""
            QLabel {
                min-width: 500 px;
                color: #b5bac1;
                font-size: 12px;
            }
        """)
        return msg

    def getAssetPath(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, 'assets', file)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"{full_path} not found.")
        return full_path

    def closeEvent(self, event):
        if self.worker.isRunning():
            self.worker.stop()
        event.accept()

class SpawnFrame():
    def __init__(self):
        app = QApplication(sys.argv)
        window = DragDropWindow()
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    SpawnFrame()

