import os
import re
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QStyle, QTextEdit, QVBoxLayout,
                             QWidget)

from zagruz.download_worker import DownloadWorker
from zagruz.update_worker import UpdateWorker


class DownloadApp(QMainWindow):
    """Main application window for the yt-dlp GUI

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
        self.url_input.setPlaceholderText("Insert URL to download")
        self.url_input.returnPressed.connect(self.start_download)

        # Format selection dropdown with label
        format_label = QLabel("Format:")
        self.format_combo: QComboBox = QComboBox()
        self.format_combo.addItems([
            "Default (best)",
            "TV (MP4, 480p)",
            "Audio (MP3, 320kbps)"
        ])
        self.format_combo.setCurrentIndex(1)  # Default to TV
        self.format_combo.setFixedWidth(150)

        # Visual separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #b0b0b0; margin: 0 10px;")

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Directory:")
        self.dir_input: QLineEdit = QLineEdit()
        self.dir_input.setReadOnly(True)
        self.dir_input.setPlaceholderText("Download directory not selected")
        self.dir_input.setText(self.download_dir)
        self.dir_input.setStyleSheet("background-color: #f0f0f0; font-style: italic;")
        self.dir_btn: QPushButton = QPushButton()
        self.dir_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.dir_btn.setToolTip("Choose download directory")

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_btn)

        # Buttons with styles
        self.download_btn: QPushButton = QPushButton(" Download")
        self.download_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.download_btn.setStyleSheet(
            "background-color: #4CAF50; color: black; padding: 5px 10px 5px 5px;")

        self.interrupt_btn: QPushButton = QPushButton(" Interrupt")
        self.interrupt_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.interrupt_btn.setStyleSheet(
            "background-color: #f44336; color: black; padding: 5px 10px 5px 5px;")

        self.update_btn: QPushButton = QPushButton(" Update")
        self.update_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.update_btn.setStyleSheet(
            "background-color: #2196F3; color: black; padding: 5px 10px 5px 5px;")

        self.open_dir_btn: QPushButton = QPushButton(" Open")
        self.open_dir_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_dir_btn.setToolTip("Open download directory")
        self.open_dir_btn.setStyleSheet(
            "background-color: #FFC107; color: black; padding: 5px 10px 5px 5px;")

        # Create horizontal lines
        url_line = QHBoxLayout()
        url_line.addWidget(self.url_input, 1)
        url_line.addWidget(self.download_btn)
        url_line.addWidget(self.interrupt_btn)
        url_line.addWidget(self.update_btn)
        url_line.addWidget(self.open_dir_btn)

        options_line = QHBoxLayout()
        options_line.addLayout(dir_layout)
        options_line.addWidget(separator)
        options_line.addWidget(format_label)
        options_line.addWidget(self.format_combo)

        # Log output area
        self.log_output: QTextEdit = QTextEdit()
        self.log_output.setReadOnly(True)

        # Assemble layout
        layout.addLayout(url_line)
        layout.addLayout(options_line)
        layout.addWidget(self.log_output)

        # Quit shortcut hint
        hint_label = QLabel("Hint: Press Ctrl+Q to quit at any time")
        hint_label.setStyleSheet("color: #666666; font-style: italic;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(hint_label)

        # Connect buttons (placeholder functions)
        self.download_btn.clicked.connect(self.start_download)
        self.dir_btn.clicked.connect(self.choose_directory)
        self.open_dir_btn.clicked.connect(self.open_directory)
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
            self.log_output.append("Error: Please enter a URL")
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

        self.download_thread = DownloadWorker(url, self.download_dir, self.format_combo.currentText())
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

    def open_directory(self) -> None:
        """Open download directory in system file explorer"""
        if not os.path.isdir(self.download_dir):
            self.log_output.append(f"Error: Directory does not exist - {self.download_dir}")
            return

        # Use Qt's platform-agnostic URL opening
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.download_dir))

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
