import json
import os
import shutil
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
        self.downloader.download_progress.connect(self._handle_download_progress)

    @override
    def run(self) -> None:
        """Main application update logic"""
        self.output.emit(self.tr("[update] Starting app update..."))
        try:
            with self._temp_dir() as tmpdir:
                latest_version, download_url, download_name = self.get_release_metadata()

                if not self.is_update_available(latest_version):
                    self.finished.emit(True)
                    return

                self.output.emit(self.tr("[update] Downloading update from ") + f"'{download_url}'")
                download_path = self.downloader.download_file(download_url, os.path.join(tmpdir, download_name))

                self.output.emit(self.tr("[update] Installing app..."))
                self.install(download_path)

                self.finished.emit(True)
        except Exception as e:
            self.output.emit(self.tr("[update] Error: ") + str(e))
            self.finished.emit(False)

    def get_release_metadata(self) -> (str, str):
        with urlopen("https://api.github.com/repos/yahorni/zagruz/releases/latest", timeout=15) as response:
            data = json.load(response)

        latest_version = data["tag_name"].lstrip('v')
        asset = next(a for a in data["assets"] if
                     ("windows" in a["name"].lower() and sys.platform == "win32") or
                     ("linux" in a["name"].lower() and sys.platform == "linux"))
        download_url = asset["browser_download_url"]
        download_name = asset["name"]
        return latest_version, download_url, download_name

    def is_update_available(self, latest_version: str) -> bool:
        """Check for available updates"""
        self.output.emit(self.tr("[update] Checking for updates..."))

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
        self.output.emit(self.tr("[update] Downloading... ") + f"{percent}% ({speed_mb:.2f} MB/s, {elapsed:.1f}s)")

    def install(self, new_exe_path: str) -> None:
        """Replace current executable with updated version"""

        if not os.path.exists(new_exe_path):
            raise FileNotFoundError(self.tr("Updated binary not found"))

        dest_dir = os.path.dirname(sys.executable)
        new_exe_name = os.path.basename(new_exe_path)
        dest_path = os.path.join(dest_dir, new_exe_name)
        shutil.move(new_exe_path, dest_path)
        self.output.emit(self.tr("[update] Update complete. New binary installed as ") + f"'{new_exe_name}'. ")
