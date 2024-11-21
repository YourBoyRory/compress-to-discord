import sys
import time
import os
import json
import subprocess
from compress2cord import VideoCompressor
from PyQt5.QtCore import Qt, QThread, QSize,  pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDoubleValidator, QDropEvent, QMovie, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox, QPushButton, QDialog, QComboBox, QLineEdit, QSpacerItem, QSizePolicy

class Compess(QThread):
    # A signal to send the result back to the main thread
    finished = pyqtSignal(str)

    def __init__(self, window, options):
        super().__init__()
        self.SIZE = int(float(options["target_size_bytes"])/1024/1024)
        self.compressor = VideoCompressor(options["target_size_bytes"], options["profile"], options["video_codec"], options["audio_codec"])
        self.window = window

    def setBatch(self, urls):
        self.urls = urls
        
    def setOptions(self, options):
        self.SIZE = int(float(options["target_size_bytes"])/1024/1024)
        self.compressor = VideoCompressor(options["target_size_bytes"], options["profile"], options["video_codec"], options["audio_codec"])

    def run(self):
        count=1
        for file in self.urls:
            self.window.label.setText(f"[{count}/{len(self.urls)}] Compressing to {self.SIZE}MB...")
            self.window.label.setStyleSheet("font-size: 16px; color: gray;")
            input_file = os.path.abspath(file.toLocalFile())
            os.makedirs(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord"), exist_ok=True)
            output_file = str(os.path.join(os.path.expanduser("~"), "Videos", "compess2cord", os.path.splitext(os.path.basename(input_file))[0] + ".compressed.mp4"))
            self.compressor.compressVideo(input_file, output_file)
            count+=1
        self.finished.emit(self.compressor.log)
        self.compressor.clearLog()

class SetOptions(QDialog):
    def __init__(self, parent=None, options=None):
        super().__init__(parent)
        
        self.save = False
        
        self.options = options
        
        self.setMinimumWidth(300)
        
        self.setWindowTitle('Options')

        # Create layout
        layout = QVBoxLayout()

        # Create drop-down menus (QComboBox)
        self.combo1 = QComboBox()
        self.combo2 = QComboBox()
        self.combo3 = QComboBox()
        self.combo4 = QComboBox()

        # Populate drop-downs with example items
        self.combo1.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"])
        self.combo2.addItems(['libx264', 'libx265', 'libaom-av1', 'libvpx-vp9'])
        self.combo3.addItems(['aac', 'libopus'])
        self.combo4.addItems(['Discord (10MB)', 'Nitro (500MB)', 'Nitro Basic (50MB)', 'Custom'])

        self.combo4.currentTextChanged.connect(self.handleComboBoxChange)

        self.combo1.setCurrentText(self.options['profile'])
        self.combo2.setCurrentText(self.options['video_codec'])
        self.combo3.setCurrentText(self.options['audio_codec'])
        
        self.textField = QLineEdit(self)
        self.textField.setPlaceholderText("Custom File Size")
        self.textField.setValidator(QDoubleValidator(self))
        
        self.textField.setHidden(True)
        
        size =self.options['target_size_bytes']
        if size == 500 * 1024 * 1024:
            size_option = 'Nitro (500MB)'
        elif size == 50 * 1024 * 1024:
            size_option = 'Nitro Basic (50MB)'
        elif size == 10 * 1024 * 1024:
            size_option = 'Discord (10MB)'
        else:
            self.textField.setText(str(size/1024/1024))
            self.textField.setHidden(False) 
            size_option = 'Custom'
        
        self.combo4.setCurrentText(size_option)
        
        # Add drop-downs and labels to the layout
        
        layout.addWidget(QLabel('Profile:'))
        layout.addWidget(self.combo1)
        
        layout.addWidget(QLabel('Video Codec:'))
        layout.addWidget(self.combo2)
        
        layout.addWidget(QLabel('Audio Codec:'))
        layout.addWidget(self.combo3)
        
        layout.addWidget(QLabel('File Size:'))
        layout.addWidget(self.combo4)
        layout.addWidget(self.textField)

        # Add a button to submit the choices
        submit_button = QPushButton('Save')
        submit_button.clicked.connect(self.submit)
        layout.addWidget(submit_button)

        # Set the layout for the dialog
        self.setLayout(layout)

    def handleComboBoxChange(self, text):
        # Show the text field when "Show Text Field" is selected
        if text == "Custom":
            self.textField.setHidden(False)
        else:
            self.textField.setHidden(True)
    
    def submit(self):
        # Handle submission of selections
        choice1 = self.combo1.currentText()
        choice2 = self.combo2.currentText()
        choice3 = self.combo3.currentText()
        choice4 = self.combo4.currentText()
        
        
        if choice4 == 'Nitro (500MB)':
            SIZE = 500 * 1024 * 1024
        elif choice4 == 'Nitro Basic (50MB)':
            SIZE = 50 * 1024 * 1024
        elif choice4 =='Custom':
            val = self.textField.text()
            if val != "":
                SIZE = float(val) * 1024 * 1024
                print(float(val), SIZE)
            else:
                print("Defaulting to 10mb")
                SIZE = 10 * 1024 * 1024
        else:
            SIZE = 10 * 1024 * 1024

        self.options['target_size_bytes'] =  SIZE
        self.options['profile'] = choice1
        self.options['video_codec'] = choice2
        self.options['audio_codec'] = choice3
        self.save = True
        self.accept()  # Close the dialog when done

class DragDropWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Set the main window properties
        self.setWindowTitle("Compress2Cord")
        self.setWindowIcon(QIcon(self.getAssetPath('icon.png')))
        self.setGeometry(100, 100, 400, 300)
        self.setFixedSize(400, 300)
        self.setAcceptDrops(True)  # Enable drag-and-drop

        font_id = QFontDatabase.addApplicationFont(self.getAssetPath("ggsans.ttf"))
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        custom_font = QFont(font_family)

        self.setStyleSheet("""
            QWidget {
                background-color: #2f3136;
                color: white;
            }
            QLabel {
                color: white;
            }
        """)
        self.setFont(custom_font)

        # Add a label to display the instruction
        self.label = QLabel("Drag and drop a videos here", self)
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

        self.show_folder_btn = QPushButton("Show Output Folder")
        self.show_folder_btn.setVisible(False)
        self.show_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: gray;
                font-size: 16px;
            }
            QPushButton:hover {
                color: darkgray;
            }
        """)
        self.show_folder_btn.clicked.connect(self.showFolder)

        # Layout to hold the labels
        layout = QVBoxLayout()
        self.header_spacer = QSpacerItem(0, 0)
        layout.addItem(self.header_spacer)
        layout.addWidget(self.show_options_btn,Qt.AlignLeft)
        layout.addWidget(self.loading_label,Qt.AlignCenter)
        layout.addWidget(self.label,Qt.AlignCenter)
        layout.addWidget(self.show_folder_btn,Qt.AlignCenter)
        self.footer_spacer = QSpacerItem(0, 35)
        layout.addItem(self.footer_spacer)
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
            self.show_folder_btn.setVisible(False)
            self.show_options_btn.setVisible(False)
            self.footer_spacer.changeSize(0, 0)
            self.header_spacer.changeSize(0, 35)
            self.movie.start()  # Start the loading animation

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
        options_window = SetOptions(self, self.options)
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
                'profile': 'slow',
                'video_codec': 'libx264',
                'audio_codec': 'aac'
            }
            
    def on_loading_complete(self, log):
        self.movie.stop()  # Stop the loading animation
        self.loading_label.setVisible(False)  # Hide the loading spinner
        self.show_folder_btn.setVisible(True)
        self.show_options_btn.setVisible(True)
        self.footer_spacer.changeSize(0, 35)
        self.header_spacer.changeSize(0, 0)
        self.label.setStyleSheet("font-size: 16px; color: white;")
        msg = self.make_popup_window(None, "Report", log, "")
        self.label.setText(f"Files Compessed\nDrag and drop more videos here")  # Show the file path
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
                min-width:500 px;
                font-size: 12pt;
            }
        """)
        return msg

    def getAssetPath(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DragDropWindow()
    window.show()
    sys.exit(app.exec_())

