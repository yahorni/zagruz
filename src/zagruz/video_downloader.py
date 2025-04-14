import os
import subprocess
from typing import override

from PyQt6.QtCore import QThread, pyqtSignal
from yt_dlp import YoutubeDL


class VideoDownloader(QThread):
    """A QThread subclass that handles video downloads in the background

    Attributes:
        output: Signal emitted for real-time download output
        finished: Signal emitted when download completes or fails
        url: The video URL to download
        directory: Target directory for downloaded files
    """

    output: pyqtSignal = pyqtSignal(str)
    finished: pyqtSignal = pyqtSignal(bool)

    def __init__(self, url: str, directory: str, format: str) -> None:
        """Initialize download worker with target URL and directory

        Args:
            url: Video URL to download
            directory: Output directory for downloaded files
            format: Selected format preset
        """
        super().__init__()
        self.url: str = url
        self.directory: str = directory
        self.format: str = format
        self.process: subprocess.Popen[str] | None = None
        self.should_stop: bool = False

    @override
    def run(self) -> None:
        """Main thread execution method that runs the yt-dlp process"""

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
            'outtmpl': os.path.join(self.directory, self.get_title_format()),
            'format': self.get_ytdlp_format(),
            'addmetadata': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }] if self.format == "audio" else [],
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

    def get_ytdlp_format(self) -> str | None:
        """Return yt-dlp format string based on selected preset"""
        if self.format == "tv":
            return "bestvideo[vcodec^=avc][height<=480][ext=mp4]+bestaudio[ext=mp4]"
        if self.format == "audio":
            return "bestaudio"
        return None

    def get_title_format(self) -> str:
        """Return yt-dlp filename based on selected preset and given link"""
        playlist_format = '%(playlist_index)s'
        title_format = '%(title)s.%(ext)s'
        if 'playlist?list' in self.url:
            if self.format == "audio":
                return playlist_format + ". %(uploader)s - " + title_format
            else:
                return playlist_format + ". " + title_format
        else:
            return title_format
