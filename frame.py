import sys
import time
import os
import json
import subprocess
from compress2cord import VideoCompressor
from PyQt5.QtCore import Qt, QThread, QSize,  pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDoubleValidator, QDropEvent, QMovie, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import QFrame, QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox, QPushButton, QDialog, QComboBox, QLineEdit, QSpacerItem, QSizePolicy

class StyleSheets():
    def getAssetPath(file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)

    image = getAssetPath("arrow.png")

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
        self.SIZE = int(float(options["target_size_bytes"])/1024/1024)
        self.compressor = VideoCompressor(options["target_size_bytes"], options["preset"], options["profile"], options["video_codec"], options["audio_codec"])
        self.window = window

    def getCodecs(self):
        return self.compressor.getCodecs()

    def setBatch(self, urls):
        self.urls = urls

    def setOptions(self, options):
        self.SIZE = int(float(options["target_size_bytes"])/1024/1024)
        self.compressor = VideoCompressor(options["target_size_bytes"], options["preset"], options["profile"], options["video_codec"], options["audio_codec"])

    def run(self):
        count=1
        for file in self.urls:
            self.window.show_folder_btn.setText(f"[{count}/{len(self.urls)}] Compressing to {self.SIZE}MB...")
            input_file = os.path.abspath(file.toLocalFile())
            os.makedirs(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord"), exist_ok=True)
            output_file = str(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord", os.path.splitext(os.path.basename(input_file))[0] + ".compressed.mp4"))
            self.compressor.compressVideo(input_file, output_file)
            count+=1
            
        self.finished.emit(self.compressor.log, self.compressor.videosCompessed, self.compressor.videosFailed, self.compressor.videosSkipped)
        self.compressor.clearLog()

class SetOptions(QDialog):
    def __init__(self, parent=None, options=None, codecs=None):
        super().__init__(parent)

        self.save = False

        self.options = options
        stylesheets = StyleSheets()
        self.setStyleSheet(stylesheets.options_stylesheet)

        self.setMinimumWidth(300)
        self.resize(400, 300)
        self.setWindowTitle('Options')

        # Create layout
        layout = QVBoxLayout()


        # Create drop-down menus (QComboBox)
        self.preset = QComboBox()
        self.profile = QComboBox()
        self.v_codec = QComboBox()
        self.a_codec = QComboBox()
        self.size = QComboBox()

        # Populate drop-downs with example items
        self.preset.addItems(["fast", "medium", "slow"])
        self.profile.addItems(["baseline", "main", "high"])
        self.v_codec.addItems(codecs['video'])
        self.a_codec.addItems(codecs['audio'])
        self.size.addItems(['Nitro (500MB)', 'Nitro Basic (50MB)', 'Discord (10MB)', 'Custom'])

        self.size.currentTextChanged.connect(self.sizeChange)
        #self.combo2.currentTextChanged.connect(self.v_codecChange)
        
        self.preset.setCurrentText(self.options['preset'])
        self.profile.setCurrentText(self.options['profile'])
        self.v_codec.setCurrentText(self.options['video_codec'])
        #self.v_codecChange(self.options['v_codec'])
        self.a_codec.setCurrentText(self.options['audio_codec'])

        self.custSizeField = QLineEdit(self)
        self.custSizeField.setPlaceholderText("Custom File Size (MB)")
        self.custSizeField.setValidator(QDoubleValidator(self))

        self.custSizeField.setHidden(True)


        size = self.options['target_size_bytes']
        if size == 500 * 1024 * 1024:
            size_option = 'Nitro (500MB)'
        elif size == 50 * 1024 * 1024:
            size_option = 'Nitro Basic (50MB)'
        elif size == 10 * 1024 * 1024:
            size_option = 'Discord (10MB)'
        else:
            self.custSizeField.setText(str(size/1024/1024))
            self.custSizeField.setHidden(False)
            size_option = 'Custom'

        self.size.setCurrentText(size_option)
        layout.setSpacing(15)
        layout.setContentsMargins(48, 24, 48, 24)
        # Add drop-downs and labels to the layout

        lable = QLabel('Compression Settings')
        lable.setStyleSheet("""
            QLabel {
                color: #f2f3f5;
                font-size: 16px;
            }
        """)
        layout.addWidget(lable)


        layout.addWidget(QLabel('SPEED'))
        layout.addWidget(self.preset)

        spacer = QSpacerItem(0, 8)
        layout.addItem(spacer)

        layout.addWidget(QLabel('PROFILE'))
        layout.addWidget(self.profile)

        spacer = QSpacerItem(0, 8)
        layout.addItem(spacer)

        layout.addWidget(QLabel('VIDEO CODEC'))
        layout.addWidget(self.v_codec)

        spacer = QSpacerItem(0, 8)
        layout.addItem(spacer)

        layout.addWidget(QLabel('AUDIO CODEC'))
        layout.addWidget(self.a_codec)

        spacer = QSpacerItem(0, 8)
        layout.addItem(spacer)

        layout.addWidget(QLabel('FILE SIZE'))
        layout.addWidget(self.size)
        layout.addWidget(self.custSizeField)

        spacer = QSpacerItem(0, 16)
        layout.addItem(spacer)

        # Add a button to submit the choices
        submit_button = QPushButton('Save')
        submit_button.clicked.connect(self.submit)
        submit_button.setMaximumWidth(90)
        layout.addWidget(submit_button, Qt.AlignCenter)

        layout.addStretch()

        # Set the layout for the dialog
        self.setLayout(layout)

    def sizeChange(self, text):
        if text == "Custom":
            self.custSizeField.setHidden(False)
        else:
            self.custSizeField.setHidden(True)
            
    def v_codecChange(self, text):
        hdot = [
            '264',
            '265',
            'hevc'
        ]
        if any(sub in text for sub in hdot):
            self.textField.setHidden(True)
            combo5.clear() 
            self.combo5.addItems(["baseline", "main", "high"])
        elif "av1" in text:
            self.textField.setHidden(True)
            combo5.clear() 
            self.combo5.addItems(["main", "high"])

    def submit(self):
        # Handle submission of selections
        choice_preset = self.preset.currentText()
        choice_profile = self.profile.currentText()
        choice_v_codec = self.v_codec.currentText()
        choice_a_codec = self.a_codec.currentText()
        choice_size = self.size.currentText()

        if choice_size == 'Nitro (500MB)':
            SIZE = 500 * 1024 * 1024
        elif choice_size == 'Nitro Basic (50MB)':
            SIZE = 50 * 1024 * 1024
        elif choice_size =='Custom':
            val = self.custSizeField.text()
            if val != "":
                SIZE = float(val) * 1024 * 1024
                print(float(val), SIZE)
            else:
                print("Defaulting to 10mb")
                SIZE = 10 * 1024 * 1024
        else:
            SIZE = 10 * 1024 * 1024

        self.options['target_size_bytes'] =  SIZE
        self.options['preset'] = choice_preset
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
        self.setWindowIcon(QIcon(self.getAssetPath('icon.png')))
        self.setGeometry(100, 100, 400, 300)
        self.setFixedSize(600, 400)
        self.setAcceptDrops(True)  # Enable drag-and-drop

        font_id = QFontDatabase.addApplicationFont(self.getAssetPath("ggsans.ttf"))
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        custom_font = QFont(font_family)

        self.stylesheets = StyleSheets()
        self.setStyleSheet(self.stylesheets.main_stylesheet)

        self.setFont(custom_font)

        # Add a label to display the instruction
        self.label = QLabel("Drag and drop your videos here", self)
        self.label.setStyleSheet("font-size: 16px; color: white;")
        self.label.setAlignment(Qt.AlignCenter)

        # Add a QLabel for the loading animation
        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignCenter)

        # Set up the loading animation (spinning wheel)
        self.movie = QMovie(self.getAssetPath("loading.gif"))  # Replace with path to your loading GIF
        self.loading_label.setMovie(self.movie)

        self.show_options_btn = QPushButton("")
        self.show_options_btn.setIcon(QIcon(self.getAssetPath('settings.png')))
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
        self.show_folder_btn.setIcon(QIcon(self.getAssetPath('file.png')))
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
            self.show_folder_btn.setIconSize(QSize(0, 0))
            self.label.setVisible(False)
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
        options_window = SetOptions(self, self.options, self.worker.getCodecs())
        options_window.exec_()
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
                'target_size_bytes': 10 * 1024 * 1024,
                'preset': 'slow',
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
        self.label.setVisible(True)
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
        return os.path.join(base_path, 'assets', file)

class SpawnFrame():
    def __init__(self):
        app = QApplication(sys.argv)
        window = DragDropWindow()
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DragDropWindow()
    window.show()
    sys.exit(app.exec_())

