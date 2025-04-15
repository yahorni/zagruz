import json
import os
import platform
import shutil
import sys
import tarfile
import zipfile
from typing import override
from urllib.request import urlopen

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
                self.output.emit(self.tr("[update] Getting last release information..."))
                latest_version, download_url, download_name = self.get_release_metadata()

                self.output.emit(self.tr("[update] Checking if update is available..."))
                if not self.is_update_available(latest_version):
                    self.finished.emit(True)
                    return

                self.output.emit(self.tr("[update] Downloading update from ") + f"'{download_url}'")
                download_path = self.downloader.download_file(download_url, os.path.join(tmpdir, download_name))

                self.output.emit(self.tr("[update] Installing app..."))
                self.install(download_path)

                self.finished.emit(True)
        except Exception as e:
            msg = str(e) if str(e) else self.tr("Unknown error") + f" ({repr(e)})"
            self.output.emit(self.tr("[update] Error: ") + msg)
            self.finished.emit(False)

    def get_release_metadata(self) -> (str, str):
        with urlopen("https://api.github.com/repos/yahorni/zagruz/releases/latest", timeout=15) as response:
            data = json.load(response)

        latest_version = data["tag_name"].lstrip('v')
        assets = [a for a in data["assets"] if
                  ("zagruz-win" in a["name"] and sys.platform == "win32") or
                  ("zagruz-linux" in a["name"] and sys.platform == "linux")]
        if not assets:
            raise ValueError(self.tr("No compatible release asset found for platform: ") + sys.platform)
        download_url = assets[0]["browser_download_url"]
        download_name = assets[0]["name"]
        return latest_version, download_url, download_name

    def is_update_available(self, latest_version: str) -> bool:
        """Check for available updates"""
        def parse_version(version_str):
            return tuple(map(int, version_str.split('.')))

        current_v = parse_version(__version__)
        latest_v = parse_version(latest_version)
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
        self.output.emit(self.tr("[update] App installed as ") + f"'{new_exe_name}'. ")

        if platform.system() != "Windows":
            os.chmod(dest_path, 0o755)
            self.output.emit(self.tr("[update] Set executable permissions"))
