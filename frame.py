import sys
import time
import os
import subprocess
from compress2cord import VideoCompressor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QMovie, QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox, QPushButton

class Compess(QThread):
    # A signal to send the result back to the main thread
    finished = pyqtSignal(str, str)

    def __init__(self, window):
        super().__init__()
        SIZE = 10 * 1024 * 1024
        self.compressor = VideoCompressor(SIZE, "fast", "libx264", "aac")
        self.window = window

    def setBatch(self, urls):
        self.urls = urls

    def run(self):
        print("Thread: Locked")
        count=1
        for file in self.urls:
            self.window.label.setText(f"[{count}/{len(self.urls)}] Compressing...")
            self.window.label.setStyleSheet("font-size: 16px; color: gray;")
            print(file.toLocalFile())
            self.compressor.compressVideo(os.path.abspath(file.toLocalFile()), 1)
            count+=1
        print("Thread: Unlocked")
        print(self.compressor.lastPath)
        self.finished.emit(self.compressor.log, self.compressor.lastPath)
        self.compressor.clearLog()

class DragDropWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("Convert2Cord")
        self.setGeometry(100, 100, 400, 300)
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

        self.show_folder_btn = QPushButton("Show Folder")
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
        layout.addWidget(self.loading_label,Qt.AlignCenter)
        layout.addWidget(self.label,Qt.AlignCenter)
        layout.addWidget(self.show_folder_btn,Qt.AlignCenter)
        self.setLayout(layout)

        # Hide the loading label initially
        self.worker = Compess(self)
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
            self.movie.start()  # Start the loading animation

            self.worker.setBatch(urls)
            self.worker.start()

            #self.worker = threading.Thread(target=self.compress, args=(urls,))
            #self.worker.start()

    def showFolder(self):
        print("Folder:", self.lastPath)
        try:
            if os.name == 'nt':
                # Use explorer to open the folder
                subprocess.run(["explorer", self.lastPath])
            else:
                # Use the default file manager (e.g., nautilus, thunar, dolphin, etc.)
                subprocess.run(["xdg-open", self.lastPath])
        except:
            print(f"ERROR: subprocess didn't work {os.name}, {self.lastPath}")

    def on_loading_complete(self, log, path):
        self.movie.stop()  # Stop the loading animation
        self.loading_label.setVisible(False)  # Hide the loading spinner
        self.show_folder_btn.setVisible(True)
        self.label.setStyleSheet("font-size: 16px; color: white;")
        msg = self.make_popup_window(None, "Report", log, "")
        self.label.setText(f"Vidoes copied to clipboard\nDrag and drop more videos here")  # Show the file path
        self.lastPath = path
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

