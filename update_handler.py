import os
import platform
import tarfile
import tempfile
import time
import urllib.request
import zipfile
import shutil
from urllib.error import URLError
from typing import override

from PyQt6.QtCore import QThread, pyqtSignal


class UpdateWorker(QThread):
    """Thread for handling FFmpeg updates"""
    output: pyqtSignal = pyqtSignal(str)
    finished: pyqtSignal = pyqtSignal(bool)

    def __init__(self, download_dir: str) -> None:
        super().__init__()
        self.should_stop: bool = False
        self.download_dir: str = download_dir

        self.dest_path: str
        self.base_url: str
        self.ffmpeg_name: str
        self.archive_type: str
        self.binary_name: str

    @override
    def run(self) -> None:
        """Main update logic"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                self._get_platform_settings()
                archive_path = self._download_ffmpeg(tmpdir)
                extracted_dir = self._extract_archive(archive_path, tmpdir)
                self._install_ffmpeg_binary(extracted_dir)
                self.output.emit(f"Successfully updated FFmpeg to latest version at {self.dest_path}")
                self.finished.emit(True)
        except URLError as e:
            self.output.emit(f"Download failed: {str(e)}")
            self.finished.emit(False)
        except Exception as e:
            self.output.emit(f"Error updating FFmpeg: {str(e)}")
            self.finished.emit(False)

    def _get_platform_settings(self) -> None:
        """Determine platform-specific settings"""
        system = platform.system()
        self.base_url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/latest/download/"

        if system == "Linux":
            self.ffmpeg_name = "ffmpeg-master-latest-linux64-gpl.tar.xz"
            self.archive_type = "tar.xz"
            self.binary_name = "ffmpeg"
        elif system == "Windows":
            self.ffmpeg_name = "ffmpeg-master-latest-win64-gpl-shared.zip"
            self.archive_type = "zip"
            self.binary_name = "ffmpeg.exe"
        else:
            self.output.emit("Error: Unsupported operating system")
            self.finished.emit(False)
            raise ValueError("Unsupported operating system")

    def _download_ffmpeg(self, tmpdir: str) -> str:
        """Handle FFmpeg download with progress reporting"""
        url = f"{self.base_url}{self.ffmpeg_name}"
        archive_path = os.path.join(tmpdir, self.ffmpeg_name)
        self.output.emit(f"Downloading FFmpeg from {url}...")

        # Progress reporting setup
        start_time = time.time()
        last_log_time = start_time
        downloaded_bytes = 0

        def reporthook(blocknum: int, blocksize: int, totalsize: int):
            nonlocal downloaded_bytes, last_log_time
            downloaded_bytes = blocknum * blocksize
            current_time = time.time()

            if current_time - last_log_time < 1.0:  # Throttle updates
                return

            last_log_time = current_time
            elapsed = current_time - start_time
            speed = downloaded_bytes / elapsed if elapsed > 0 else 0

            if totalsize > 0:
                percent = downloaded_bytes / totalsize * 100
                self.output.emit(
                    f"Download progress: {percent:.1f}% "
                    f"({downloaded_bytes/1e6:.2f} MB of {totalsize/1e6:.2f} MB) "
                    f"at {speed/1e6:.2f} MB/s"
                )
            else:
                self.output.emit(
                    f"Downloaded {downloaded_bytes/1e6:.2f} MB "
                    f"at {speed/1e6:.2f} MB/s"
                )

        actual_path, headers = urllib.request.urlretrieve(url, archive_path, reporthook)

        if actual_path != archive_path:
            raise RuntimeError(f"Download path mismatch: {actual_path} vs {archive_path}")

        self.output.emit("Download completed successfully")
        return archive_path

    def _extract_archive(self, archive_path: str, tmpdir: str) -> str:
        """Handle archive extraction based on file type"""
        self.output.emit("Extracting files...")

        if self.archive_type == "tar.xz":
            with tarfile.open(archive_path, "r:xz") as tar:
                tar.extractall(path=tmpdir, filter='data')
        elif self.archive_type == "zip":
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

        # Determine extraction directory
        extracted_dir = os.path.join(tmpdir, self.ffmpeg_name.split('.')[0])
        if not os.path.exists(extracted_dir):
            extracted_dir = tmpdir  # Fallback to temp dir

        return extracted_dir

    def _install_ffmpeg_binary(self, extracted_dir: str) -> None:
        """Install the FFmpeg binary to target directory"""
        src_path = os.path.join(extracted_dir, "bin", self.binary_name)
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"FFmpeg binary not found in {src_path}")

        self.dest_path = os.path.join(self.download_dir, self.binary_name)

        # Remove existing binary if present
        if os.path.exists(self.dest_path):
            try:
                os.remove(self.dest_path)
            except Exception as e:
                raise RuntimeError(f"Could not remove old FFmpeg: {str(e)}")

        shutil.copy(src_path, self.dest_path)

        # Set executable permissions if not Windows
        if platform.system() != "Windows":
            os.chmod(self.dest_path, 0o755)
