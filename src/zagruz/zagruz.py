import os
import re
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QStyle,
                             QTextEdit, QVBoxLayout, QWidget)

from zagruz.download_worker import DownloadWorker
from zagruz.options_dialog import OptionsDialog
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
        self.selected_format = "TV (MP4, 480p)"  # Default format
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

        self.options_btn: QPushButton = QPushButton(" Options")
        self.options_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.options_btn.setStyleSheet(
            "background-color: #9C27B0; color: black; padding: 5px 10px 5px 5px;")
        self.options_btn.setToolTip("Application settings")

        # Create horizontal lines
        url_line = QHBoxLayout()
        url_line.addWidget(self.url_input, 1)

        # Create new button line below URL input
        button_line = QHBoxLayout()
        button_line.addWidget(self.download_btn)
        button_line.addWidget(self.interrupt_btn)
        button_line.addWidget(self.update_btn)
        button_line.addWidget(self.open_dir_btn)
        button_line.addWidget(self.options_btn)

        # Log output area
        self.log_output: QTextEdit = QTextEdit()
        self.log_output.setReadOnly(True)

        # Assemble layout
        layout.addLayout(url_line)
        layout.addLayout(button_line)
        layout.addWidget(self.log_output)

        # Quit shortcut hint
        hint_label = QLabel("Hint: Press Ctrl+Q to quit at any time")
        hint_label.setStyleSheet("color: #666666; font-style: italic;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(hint_label)

        # Connect buttons (placeholder functions)
        self.download_btn.clicked.connect(self.start_download)
        self.interrupt_btn.clicked.connect(self.interrupt_download)
        self.update_btn.clicked.connect(self.update_app)
        self.open_dir_btn.clicked.connect(self.open_directory)
        self.options_btn.clicked.connect(self.show_options)

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

        self.download_thread = DownloadWorker(url, self.download_dir, self.selected_format)
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

    def show_options(self) -> None:
        """Show the options dialog window"""
        dialog = OptionsDialog(self)
        dialog.dir_input.setText(self.download_dir)
        dialog.format_combo.setCurrentText(self.selected_format)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update download directory from dialog
            new_dir = dialog.dir_input.text()
            if new_dir != self.download_dir and new_dir and os.path.isdir(new_dir):
                self.download_dir = new_dir
                self.log_output.append(f"Download directory updated to: {new_dir}")

            # Update format from dialog
            new_format = dialog.format_combo.currentText()
            if new_format != self.selected_format and new_format:
                self.selected_format = dialog.format_combo.currentText()
                self.log_output.append(f"Download format updated to: {new_format}")


def main() -> None:
    """Main entry point for the Zagruz application"""
    app = QApplication(sys.argv)
    window = DownloadApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
