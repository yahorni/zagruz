# Zagruz - yt-dlp GUI Wrapper

![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux-lightgrey)

A cross-platform GUI frontend for yt-dlp featuring:
- Multi-site URL support via yt-dlp
- Directory selection
- Real-time download logging
- Keyboard shortcuts
- Download progress monitoring

## Features
- Clean PyQt6 interface
- Smart URL validation
- Download interruption support
- Cross-platform compatibility

## Build
```bash
git clone https://github.com/yahorni/zagruz.git
cd zagruz

# Installs pyinstaller from optional-dependencies
uv pip install .[package]

# Windows executable:
uv run python -m PyInstaller package/windows.spec --noconfirm

# Linux executable:
uv run python -m PyInstaller package/linux.spec --noconfirm
```

## Dependencies
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download backend (supports 1000+ sites)

## TODO
- Binary package for linux/windows
- Preconfigured profiles of yt-dlp
- Russian localization
- `[download]` log parsing to prevent spam in output
- Directory persistence between sessions

## License
![AGPLv3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
