import tempfile
import time
import urllib.request
from typing import ContextManager

from PyQt6.QtCore import QThread, pyqtSignal, QObject


class BaseDownloader(QThread):
    """Base class for file downloaders"""
    output = pyqtSignal(str)
    finished = pyqtSignal(bool)

    class Downloader(QObject):
        """Nested QObject for download operations"""
        output = pyqtSignal(str)
        download_progress = pyqtSignal(int, float, float)  # percent, speed MB/s, elapsed

        def __init__(self):
            super().__init__()
            self.should_stop = False

        def download_file(self, url: str, dest_path: str) -> str:
            """Download a file with progress reporting"""
            start_time = time.time()
            last_log_time = start_time
            downloaded_bytes = 0
            file_size = 0

            def reporthook(blocknum: int, blocksize: int, totalsize: int):
                nonlocal downloaded_bytes, last_log_time, file_size
                file_size = totalsize
                downloaded_bytes = blocknum * blocksize
                current_time = time.time()

                if current_time - last_log_time < 1.0:  # Throttle updates
                    return

                last_log_time = current_time
                elapsed = current_time - start_time
                speed = downloaded_bytes / elapsed if elapsed > 0 else 0
                self.download_progress.emit(
                    int((downloaded_bytes / totalsize) * 100) if totalsize > 0 else 0,
                    speed / 1e6,
                    elapsed
                )

            return urllib.request.urlretrieve(url, dest_path, reporthook)[0]

    def __init__(self) -> None:
        super().__init__()
        self.should_stop = False
        self.downloader = self.Downloader()

    def run(self) -> None:
        """Subclasses must implement this method"""
        raise NotImplementedError("run() method must be implemented in subclass")

    def _temp_dir(self) -> ContextManager[str]:
        """Create temporary directory with cleanup"""
        return tempfile.TemporaryDirectory()
