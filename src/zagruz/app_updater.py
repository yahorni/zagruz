import json
import os
import sys
import tarfile
import zipfile
from typing import override
from urllib.request import urlopen

from packaging import version

from zagruz import __version__
from zagruz.base_downloader import BaseDownloader


class AppUpdater(BaseDownloader):
    """Handles application updates"""

    def __init__(self) -> None:
        super().__init__()
        self.binary_name = "zagruz-linux" if sys.platform == "linux" else "zagruz-win.exe"
        self.expected_name = self.binary_name
        self.downloader.download_progress.connect(self._handle_download_progress)

    @override
    def run(self) -> None:
        """Main application update logic"""
        self.output.emit(self.tr("[update] Starting app update..."))
        try:
            with self._temp_dir() as tmpdir:
                with urlopen("https://api.github.com/repos/yahorni/zagruz/releases/latest", timeout=15) as response:
                    data = json.load(response)

                if not self.is_update_available(data):
                    self.finished.emit(True)
                    return

                download_path = self.download(tmpdir, data)
                extracted_dir = self.extract(download_path, tmpdir)
                self.install(extracted_dir)
                self.finished.emit(True)
        except Exception as e:
            self.output.emit(f"[update] Error: {str(e)}")
            self.finished.emit(False)

    def is_update_available(self, data) -> bool:
        """Check for available updates"""
        self.output.emit(self.tr("[update] Checking for updates..."))

        latest_version = data["tag_name"].lstrip('v')
        current_v = version.parse(__version__)
        latest_v = version.parse(latest_version)

        if current_v > latest_v:
            self.output.emit(self.tr("[update] Development version detected "))
            return False
        if current_v == latest_v:
            self.output.emit(self.tr("[update] Already up-to-date"))
            return False

        self.output.emit(self.tr("[update] Found update: ") + latest_version)
        return True

    def download(self, tmpdir: str, data) -> str:
        """Download latest app version"""
        asset = next(a for a in data["assets"] if
                     ("windows" in a["name"].lower() and sys.platform == "win32") or
                     ("linux" in a["name"].lower() and sys.platform == "linux"))
        download_url = asset["browser_download_url"]

        self.output.emit(self.tr("[update] Downloading update..."))
        return self.downloader.download_file(download_url, os.path.join(tmpdir, asset["name"]))

    def extract(self, archive_path: str, tmpdir: str) -> str:
        """Extract the downloaded package"""
        if sys.platform == "win32":
            with zipfile.ZipFile(archive_path) as zip_ref:
                zip_ref.extractall(tmpdir)
        else:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(tmpdir)

        bin_dir = os.path.join(tmpdir, "zagruz" if sys.platform == "linux" else "")
        if not os.path.exists(bin_dir):
            raise FileNotFoundError(self.tr("Invalid update package structure"))

        return bin_dir

    def _handle_download_progress(self, percent: int, speed_mb: float, elapsed: float) -> None:
        """Handle download progress updates"""
        self.output.emit(self.tr(f"[update] Downloading... {percent}% ({speed_mb:.2f} MB/s, {elapsed:.1f}s)"))

    def install(self, extracted_dir: str) -> None:
        """Replace current executable with updated version"""
        current_exe = sys.executable
        new_exe_path = os.path.join(extracted_dir, self.expected_name)

        if not os.path.exists(new_exe_path):
            raise FileNotFoundError(self.tr("Updated binary not found"))

        os.replace(new_exe_path, current_exe)
        self.output.emit(self.tr("[update] Update complete. Restart application"))
