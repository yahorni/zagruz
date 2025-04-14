import os
import platform
import shutil
import sys
import tarfile
import zipfile
from typing import override

from zagruz.base_downloader import BaseDownloader


class FFmpegInstaller(BaseDownloader):
    """Handles FFmpeg dependency"""

    def __init__(self) -> None:
        super().__init__()
        self.downloader.download_progress.connect(self._handle_download_progress)

        system = platform.system()
        self.base_url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/latest/download/"

        if system == "Windows":
            self.ffmpeg_build = "ffmpeg-master-latest-win64-gpl"
            self.archive_type = "zip"
            self.binary_name = "ffmpeg.exe"
        else:  # Linux
            self.ffmpeg_build = "ffmpeg-master-latest-linux64-gpl"
            self.archive_type = "tar.xz"
            self.binary_name = "ffmpeg"

        self.archive_name = f"{self.ffmpeg_build}.{self.archive_type}"

    def _is_ffmpeg_installed(self) -> bool:
        """Check if FFmpeg is already installed and accessible"""
        return bool(shutil.which('ffmpeg'))

    @override
    def run(self) -> None:
        """Main FFmpeg install logic"""
        if self._is_ffmpeg_installed():
            self.output.emit(self.tr("[ffmpeg] FFmpeg is already installed"))
            self.finished.emit(True)
            return

        self.output.emit(self.tr("[ffmpeg] Starting download..."))
        try:
            with self._temp_dir() as tmpdir:
                self._perform_install(tmpdir)
                self.finished.emit(True)
        except Exception as e:
            self.output.emit(f"[ffmpeg] Error: {str(e)}")
            self.finished.emit(False)

    def _perform_install(self, tmpdir: str) -> None:
        """Execute FFmpeg install workflow"""
        self.output.emit(self.tr("[ffmpeg] Downloading FFmpeg..."))
        download_path = self.downloader.download_file(
            self.base_url + self.archive_name,
            os.path.join(tmpdir, self.archive_name)
        )

        self.output.emit(self.tr("[ffmpeg] Extracting archive..."))
        self._extract_archive(download_path, tmpdir)

        self.output.emit(self.tr("[ffmpeg] Installing FFmpeg..."))
        self._install_binary(os.path.join(tmpdir, self.ffmpeg_build))

    def _extract_archive(self, archive_path: str, tmpdir: str) -> None:
        """Extract downloaded FFmpeg archive"""
        if self.archive_type == "zip":
            with zipfile.ZipFile(archive_path) as zip_ref:
                zip_ref.extractall(tmpdir)
        else:
            with tarfile.open(archive_path, "r:xz") as tar:
                tar.extractall(tmpdir)

    def _handle_download_progress(self, percent: int, speed_mb: float, elapsed: float) -> None:
        """Handle download progress updates"""
        self.output.emit(self.tr(f"[ffmpeg] Downloading... {percent}% ({speed_mb:.2f} MB/s, {elapsed:.1f}s)"))

    def _install_binary(self, extracted_dir: str) -> None:
        """Install the FFmpeg binary to system location"""
        src_path = os.path.join(extracted_dir, "bin", self.binary_name)
        if not os.path.exists(src_path):
            raise FileNotFoundError(self.tr("FFmpeg binary not found in download package"))

        # Get installation directory (same as executable location)
        # TODO: test for dev/wheel/package
        install_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
        dest_path = os.path.join(install_dir, self.binary_name)
        self.output.emit(self.tr("[ffmpeg] Installing to: ") + dest_path)

        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception as e:
                raise RuntimeError(self.tr("Could not remove old FFmpeg: ") + str(e))

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(src_path, dest_path)
        self.output.emit(self.tr("[ffmpeg] FFmpeg installed successfully"))

        if platform.system() != "Windows":
            os.chmod(dest_path, 0o755)
            self.output.emit(self.tr("[ffmpeg] Set executable permissions"))
