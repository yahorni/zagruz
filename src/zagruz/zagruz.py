import os
import re
import shutil
import sys
from importlib.resources import files
from pathlib import Path

import qdarktheme
from PyQt6.QtCore import QSettings, Qt, QTranslator, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QIcon
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog,
                             QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QPushButton, QStyle, QTextEdit,
                             QVBoxLayout, QWidget)

from zagruz import __version__
from zagruz.app_updater import AppUpdater
from zagruz.ffmpeg_installer import FFmpegInstaller
from zagruz.options import (download_dir_options, format_options, lang_options,
                            theme_options)
from zagruz.options_dialog import OptionsDialog
from zagruz.video_downloader import VideoDownloader


class DownloadApp(QMainWindow):
    """Main application window for the yt-dlp GUI

    Attributes:
        download_thread: Current active download thread
        download_dir: Currently selected download directory
    """

    def __init__(self, ui: bool = True) -> None:
        super().__init__()

        self.translator = QTranslator()
        self.update_in_progress: bool = False

        self.download_thread: VideoDownloader | None = None
        self.update_thread: AppUpdater | None = None

        if ui:
            self.init_ui()
            self.apply_theme(theme_options.selected)
            self.apply_language(lang_options.selected)
            self.retranslateUi()
            self.check_ffmpeg_requirement()

    def init_ui(self) -> None:
        """Initialize and arrange all UI components"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # URL input with placeholder
        self.url_input: QLineEdit = QLineEdit()
        self.url_input.setPlaceholderText(self.tr("Insert URL to download"))
        self.url_input.returnPressed.connect(self.start_download)

        # Buttons with styles
        self.download_btn: QPushButton = QPushButton(self.tr(" Download"))
        self.download_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.download_btn.setToolTip(self.tr("Download video/audio"))
        self.download_btn.setDefault(True)
        self.download_btn.setCheckable(True)
        self.download_btn.clicked.connect(self.toggle_download_action)

        self.open_dir_btn: QPushButton = QPushButton(self.tr(" Open"))
        self.open_dir_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_dir_btn.setToolTip(self.tr("Open download directory"))

        self.update_btn: QPushButton = QPushButton(self.tr(" Update"))
        self.update_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.update_btn.setToolTip(self.tr("Update application"))

        self.options_btn: QPushButton = QPushButton(self.tr(" Options"))
        self.options_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.options_btn.setToolTip(self.tr("Application settings"))

        # Create horizontal lines
        url_line = QHBoxLayout()
        url_line.addWidget(self.url_input, 1)

        # Create new button line below URL input
        button_line = QHBoxLayout()
        button_line.addWidget(self.download_btn)
        button_line.addWidget(self.open_dir_btn)
        button_line.addWidget(self.update_btn)
        button_line.addWidget(self.options_btn)

        # Log output area
        self.log_output: QTextEdit = QTextEdit()
        self.log_output.setReadOnly(True)

        # Version and quit hint
        bottom_layout = QHBoxLayout()

        version_label = QLabel(f"v{__version__}")
        version_label.setStyleSheet("font-style: italic; color: #666;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        hint_label = QLabel(self.tr("Hint: Press Ctrl+Q to quit"))
        hint_label.setStyleSheet("font-style: italic;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        bottom_layout.addWidget(version_label)
        bottom_layout.addWidget(hint_label)

        # Assemble layout
        layout.addLayout(url_line)
        layout.addLayout(button_line)
        layout.addWidget(self.log_output)
        layout.addLayout(bottom_layout)

        # State tracking for download button
        self.is_downloading: bool = False

        # Connect buttons (placeholder functions)
        self.update_btn.clicked.connect(self.update_app)
        self.open_dir_btn.clicked.connect(self.open_directory)
        self.options_btn.clicked.connect(self.show_options)

        # Window settings
        self.setGeometry(100, 100, 600, 400)

        # Quit shortcut
        quit_action: QAction = QAction(self.tr("Quit"), self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.addAction(quit_action)

        # Focus shortcut
        focus_action: QAction = QAction(self.tr("Focus on URL input"), self)
        focus_action.setShortcut("Ctrl+L")
        focus_action.triggered.connect(self.url_input.setFocus)
        self.addAction(focus_action)

    def start_download(self) -> None:
        """Validate inputs and start a new download thread"""
        if self.update_in_progress:
            self.log_output.append(self.tr("Please wait until the current download finishes"))
            return

        url = self.url_input.text().strip()
        if not url:
            self.log_output.append(self.tr("Error: Please enter a URL"))
            return

        if not self.validate_url(url):
            self.log_output.append(self.tr("Error: Invalid URL"))
            return

        if self.download_thread and self.download_thread.isRunning():
            self.log_output.append(self.tr("Download already in progress"))
            return

        self.is_downloading = True
        self.download_btn.setChecked(True)
        self.download_btn.setText(self.tr(" Interrupt"))
        self.download_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.log_output.append(self.tr("Starting download: ") + url)

        self.download_thread = VideoDownloader(url, download_dir_options.selected, format_options.selected)
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
        """Append download process messages to the log output"""
        self.log_output.append(message)

    def download_finished(self, success: bool) -> None:
        """Handle download completion signal from worker thread"""
        self.is_downloading = False
        self.download_btn.setChecked(False)
        self.download_btn.setText(self.tr(" Download"))
        self.download_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        if success:
            self.log_output.append(self.tr("Download completed successfully!"))
        else:
            self.log_output.append(self.tr("Download failed or interrupted"))

    def toggle_download_action(self) -> None:
        """Handle combined download/interrupt button functionality"""
        if self.is_downloading:
            self.interrupt_download()
        else:
            self.start_download()

    def interrupt_download(self) -> None:
        """Stop the current download process if active"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.log_output.append(self.tr("Download interrupted by user"))
        else:
            self.log_output.append(self.tr("No active download to interrupt"))

    def open_directory(self) -> None:
        """Open download directory in system file explorer"""
        if not os.path.isdir(download_dir_options.selected):
            self.log_output.append(self.tr("Error: Directory does not exist - ") + download_dir_options.selected)
            return

        # Use Qt's platform-agnostic URL opening
        QDesktopServices.openUrl(QUrl.fromLocalFile(download_dir_options.selected))

    def check_ffmpeg_requirement(self) -> None:
        """Check FFmpeg installation on startup and prompt user if missing"""
        if shutil.which('ffmpeg'):
            return

        settings = QSettings()
        if settings.value("ffmpeg/disablePrompt", False, type=bool):
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("FFmpeg installation"))
        layout = QVBoxLayout()

        message = QLabel(self.tr(
            "FFmpeg is required for audio conversion and some video formats.\n"
            "Would you like to install it now?"
        ))
        message.setWordWrap(True)
        layout.addWidget(message)

        dont_show_check = QCheckBox(self.tr("Don't show this message again"))
        layout.addWidget(dont_show_check)

        btn_box = QDialogButtonBox()
        yes_btn = QPushButton(self.tr("Yes"))
        no_btn = QPushButton(self.tr("No"))
        btn_box.addButton(yes_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        btn_box.addButton(no_btn, QDialogButtonBox.ButtonRole.RejectRole)
        yes_btn.clicked.connect(dialog.accept)
        no_btn.clicked.connect(dialog.reject)
        layout.addWidget(btn_box)

        dialog.setLayout(layout)

        if dont_show_check.isChecked():
            settings.setValue("ffmpeg/disablePrompt", True)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.install_ffmpeg()

    def update_app(self) -> None:
        """Start application update in a background thread"""
        if self.update_thread and self.update_thread.isRunning():
            self.log_output.append(self.tr("Please wait until the current download finishes"))
            return

        self.update_btn.setEnabled(False)
        self.update_in_progress = True

        self.update_thread = AppUpdater()
        self.update_thread.output.connect(self.handle_download_output)
        self.update_thread.finished.connect(self._update_finished)
        self.update_thread.start()

    def install_ffmpeg(self) -> None:
        """Start FFmpeg installation in a background thread"""
        if self.update_thread and self.update_thread.isRunning():
            self.log_output.append(self.tr("Please wait until the current download finishes"))
            return

        self.download_btn.setEnabled(False)
        self.update_in_progress = True

        self.update_thread = FFmpegInstaller()
        self.update_thread.output.connect(self.handle_download_output)
        self.update_thread.finished.connect(self._ffmpeg_install_finished)
        self.update_thread.start()

    def _update_finished(self, success: bool) -> None:
        """Handle app update completion"""
        self.update_btn.setEnabled(True)
        self.update_in_progress = False

    def _ffmpeg_install_finished(self, success: bool) -> None:
        """Handle FFmpeg installation completion"""
        self.download_btn.setEnabled(True)
        self.update_in_progress = False

    def show_options(self) -> None:
        """Show the options dialog window"""
        dialog = OptionsDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._update_download_directory(dialog.dir_input.text())
            self._update_format(format_options.from_value(dialog.format_combo.currentText()))
            self._update_theme(theme_options.from_value(dialog.theme_combo.currentText()))
            self._update_language(lang_options.from_value(dialog.lang_combo.currentText()))

    def _update_download_directory(self, new_dir: str) -> None:
        if new_dir != download_dir_options.selected and new_dir and os.path.isdir(new_dir):
            download_dir_options.selected = new_dir
            self.log_output.append(self.tr("Download directory updated to: ") + new_dir)

    def _update_format(self, new_format: str) -> None:
        if new_format != format_options.selected and format_options.is_valid(new_format):
            format_options.selected = new_format
            self.log_output.append(self.tr("Download format updated to: ") + format_options.selected_text)

    def _update_theme(self, new_theme: str) -> None:
        if new_theme != theme_options.selected and theme_options.is_valid(new_theme):
            theme_options.selected = new_theme
            self.apply_theme(new_theme)
            self.log_output.append(self.tr("Theme changed to: ") + theme_options.selected_text)

    def _update_language(self, new_lang: str) -> None:
        if new_lang != lang_options.selected and lang_options.is_valid(new_lang):
            lang_options.selected = new_lang
            self.apply_language(new_lang)
            self.retranslateUi()
            self.log_output.append(self.tr("Language changed to: ") + new_lang)

    def apply_theme(self, theme: str) -> None:
        """Apply selected theme using qdarktheme"""

        # Don't use full qdarktheme, just palette + stylesheets
        self.setPalette(qdarktheme.load_palette(theme))
        self.setStyleSheet(qdarktheme.load_stylesheet(theme))

        # Force refresh of all UI elements
        self.style().unpolish(self)
        self.style().polish(self)

    def apply_language(self, locale: str) -> None:
        """Load application translations"""

        lang = lang_options.to_text(locale)

        if not lang_options.is_valid(locale):
            self.log_output.append(self.tr("Unsupported language: ") + lang)
            return

        if locale == "en_US":
            QApplication.instance().removeTranslator(self.translator)
            return

        resource_path = None

        if getattr(sys, 'frozen', False):
            # PyInstaller bundled executable
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            bundled_path = os.path.join(base_path, 'translations', f"{locale}.qm")
            if os.path.exists(bundled_path):
                resource_path = bundled_path
        else:
            # Development mode using package resources
            resource_path = files("zagruz.translations").joinpath(f"{locale}.qm")
            if not resource_path.is_file():
                resource_path = None

        if not resource_path or not os.path.exists(resource_path):
            self.log_output.append(self.tr("Failed to find language file: ") + lang)
            return

        if not self.translator.load(str(resource_path)):
            self.log_output.append(self.tr("Failed to load language: ") + lang)
            return

        QApplication.instance().installTranslator(self.translator)

    def retranslateUi(self) -> None:
        """Retranslate all UI elements"""
        self.setWindowTitle(self.tr("zagruz - yt-dlp GUI Wrapper"))
        self.url_input.setPlaceholderText(self.tr("Insert URL to download"))
        self.download_btn.setText(self.tr(" Download"))
        self.update_btn.setText(self.tr(" Update"))
        self.open_dir_btn.setText(self.tr(" Open"))
        self.options_btn.setText(self.tr(" Options"))
        self.log_output.setPlaceholderText(self.tr("Log output will appear here..."))
        for widget in self.findChildren(QLabel):
            if widget.text().startswith("Hint:"):
                widget.setText(self.tr("Hint: Press Ctrl+Q to quit"))


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle mode
        base_path = Path(sys._MEIPASS)
    else:
        # Normal development mode
        base_path = Path(__file__).parent.parent.parent

    return str(base_path / relative_path)


def main() -> None:
    """Main entry point for the zagruz application"""
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    app.setOrganizationName("zagruz")
    app.setApplicationName("zagruz")
    app.setWindowIcon(QIcon(get_resource_path("assets/icon.ico")))
    if sys.platform == "win32":
        app.setStyle("Windows")
    window = DownloadApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
