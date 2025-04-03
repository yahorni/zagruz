import os
import re
import subprocess
import sys
from typing import override

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QTextEdit,
                             QVBoxLayout, QWidget)

from zagruz.update_handler import UpdateWorker


class DownloadWorker(QThread):
    """A QThread subclass that handles video downloads in the background

    Attributes:
        output: Signal emitted for real-time download output
        finished: Signal emitted when download completes or fails
        url: The video URL to download
        directory: Target directory for downloaded files
    """

    output: pyqtSignal = pyqtSignal(str)
    finished: pyqtSignal = pyqtSignal(bool)

    def __init__(self, url: str, directory: str) -> None:
        """Initialize download worker with target URL and directory

        Args:
            url: Video URL to download
            directory: Output directory for downloaded files
        """
        super().__init__()
        self.url: str = url
        self.directory: str = directory
        self.process: subprocess.Popen[str] | None = None
        self.should_stop: bool = False

    @override
    def run(self) -> None:
        """Main thread execution method that runs the yt-dlp process"""
        from yt_dlp import YoutubeDL

        class ProgressLogger:
            def __init__(self, output_signal: pyqtSignal):
                self.output_signal: pyqtSignal = output_signal

            def debug(self, msg: str):
                if not msg.startswith('[debug]'):
                    self.output_signal.emit(msg)

            def info(self, msg: str):
                self.output_signal.emit(msg)

            def warning(self, msg: str):
                self.output_signal.emit(f"Warning: {msg}")

            def error(self, msg: str):
                self.output_signal.emit(f"Error: {msg}")

        self.should_stop = False

        def progress_hook(_) -> None:
            if self.should_stop:
                raise Exception("Download interrupted by user")

        ydl_opts = {
            'outtmpl': os.path.join(self.directory, '%(title)s.%(ext)s'),
            'format': 'bestvideo[vcodec^=avc][height<=480][ext=mp4]+bestaudio[ext=mp4]',
            'addmetadata': True,
            'logger': ProgressLogger(self.output),
            'progress_hooks': [progress_hook],
            # Disable ANSI escape codes at source
            'no_color': True,
            'progress_with_newline': True,
            'console_title': False
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit(True)
        except Exception as e:
            if self.should_stop:
                self.output.emit("Download interrupted by user")
            else:
                self.output.emit(f"Error: {str(e)}")
            self.finished.emit(False)

    def stop(self) -> None:
        """Gracefully stop the download process if running"""
        self.should_stop = True


class DownloadApp(QMainWindow):
    """Main application window for the YouTube downloader GUI

    Attributes:
        download_thread: Current active download thread
        download_dir: Currently selected download directory
    """

    def __init__(self, ui: bool = True) -> None:
        super().__init__()
        self.download_thread: DownloadWorker | None = None
        self.download_dir: str = os.getcwd()
        if ui:
            self.init_ui()

    def init_ui(self) -> None:
        """Initialize and arrange all UI components"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # URL input with placeholder
        self.url_input: QLineEdit = QLineEdit()
        self.url_input.setPlaceholderText("Insert YouTube link to download")
        self.url_input.returnPressed.connect(self.start_download)

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Download Directory:")
        self.dir_input: QLineEdit = QLineEdit()
        self.dir_input.setReadOnly(True)
        self.dir_input.setPlaceholderText("Download directory not selected")
        self.dir_input.setText(self.download_dir)
        self.dir_input.setStyleSheet("background-color: #f0f0f0; font-style: italic;")
        self.dir_btn: QPushButton = QPushButton("Choose Directory")
        self.dir_btn.setStyleSheet("background-color: #FFA500; color: white;")
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_btn)

        # Buttons with styles
        self.download_btn: QPushButton = QPushButton("Download")
        self.download_btn.setStyleSheet(
            "background-color: #4CAF50; color: white;")

        self.interrupt_btn: QPushButton = QPushButton("Interrupt")
        self.interrupt_btn.setStyleSheet(
            "background-color: #f44336; color: white;")

        self.update_btn: QPushButton = QPushButton("Update")
        self.update_btn.setStyleSheet(
            "background-color: #2196F3; color: white;")

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.interrupt_btn)
        button_layout.addWidget(self.update_btn)

        # Log output area
        self.log_output: QTextEdit = QTextEdit()
        self.log_output.setReadOnly(True)

        # Assemble layout
        layout.addWidget(self.url_input)
        layout.addLayout(button_layout)
        layout.addLayout(dir_layout)  # Add directory selection row
        layout.addWidget(self.log_output)

        # Quit shortcut hint
        hint_label = QLabel("Hint: Press Ctrl+Q to quit at any time")
        hint_label.setStyleSheet("color: #666666; font-style: italic;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(hint_label)

        # Connect buttons (placeholder functions)
        self.download_btn.clicked.connect(self.start_download)
        self.dir_btn.clicked.connect(self.choose_directory)
        self.interrupt_btn.clicked.connect(self.interrupt_download)
        self.update_btn.clicked.connect(self.update_app)

        # Window settings
        self.setWindowTitle("Zagruz - yt-dlp GUI Wrapper")
        self.setGeometry(100, 100, 600, 400)

        # Quit shortcut
        quit_action: QAction = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.addAction(quit_action)

        # Focus shortcut
        focus_action: QAction = QAction("Focus on URL input", self)
        focus_action.setShortcut("Ctrl+L")
        focus_action.triggered.connect(self.url_input.setFocus)
        self.addAction(focus_action)

    def start_download(self) -> None:
        """Validate inputs and start a new download thread"""
        url = self.url_input.text().strip()
        if not url:
            self.log_output.append("Error: Please enter a YouTube URL")
            return

        if not self.validate_url(url):
            self.log_output.append("Error: Invalid URL")
            return

        if self.download_thread and self.download_thread.isRunning():
            self.log_output.append("Download already in progress")
            return

        self.log_output.append(f"Starting download: {url}")
        self.download_btn.setEnabled(False)

        if not self.download_dir:
            self.log_output.append("Error: Please select a download directory")
            return

        self.download_thread = DownloadWorker(url, self.download_dir)
        self.download_thread.output.connect(self.handle_download_output)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def validate_url(self, url: str) -> bool:
        """Validate HTTP/HTTPS URLs with basic pattern matching

        Args:
            url: The URL string to validate

        Returns:
            bool: True if URL matches valid HTTP/HTTPS pattern, False otherwise
        """
        pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:[^/:@]+(?::[^/@]*)?@)?"  # user:pass@
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IPv4
            r"(?::\d+)?"  # port
            r"(?:/[\w~%!$&'()*+,;=:@.-]*)*"  # path
            r"(?:\?[\w~%!$&'()*+,;=:@/?-]*)?"  # query
            r"(?:\#[\w~%!$&'()*+,;=:@/?-]*)?$",  # fragment (escaped #)
            re.IGNORECASE
        )
        return pattern.fullmatch(url) is not None

    def handle_download_output(self, message: str) -> None:
        """Append download process messages to the log output

        Args:
            message: Progress message from download thread
        """
        self.log_output.append(message)

    def download_finished(self, success: bool) -> None:
        """Handle download completion signal from worker thread.

        Args:
            success: True if download completed successfully, False otherwise
        """
        self.download_btn.setEnabled(True)
        if success:
            self.log_output.append("Download completed successfully!")
        else:
            self.log_output.append("Download failed or interrupted")

    def interrupt_download(self) -> None:
        """Stop the current download process if active"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.log_output.append("Download interrupted by user")
            self.download_btn.setEnabled(True)
        else:
            self.log_output.append("No active download to interrupt")

    def choose_directory(self) -> None:
        """Open directory dialog and set download path"""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir = directory
            self.dir_input.setText(directory)
            self.log_output.append(f"Download directory set to: {directory}")

    def update_app(self) -> None:
        """Start FFmpeg update in a background thread"""
        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            self.log_output.append("Update already in progress")
            return

        self.update_btn.setEnabled(False)
        self.log_output.append("Starting FFmpeg update...")
        self.update_thread = UpdateWorker(self.download_dir)
        self.update_thread.output.connect(self.handle_download_output)
        self.update_thread.finished.connect(self.update_finished)
        self.update_thread.start()

    def update_finished(self, success: bool) -> None:
        """Handle update completion"""
        self.update_btn.setEnabled(True)
        if success:
            self.log_output.append("FFmpeg update completed successfully!")
        else:
            self.log_output.append("FFmpeg update failed")


def main() -> None:
    """Main entry point for the Zagruz application"""
    app = QApplication(sys.argv)
    window = DownloadApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
