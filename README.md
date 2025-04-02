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
- Directory persistence between sessions

## Installation
```bash
# Requires Python 3.12+
python -m pip install pyqt6 yt-dlp
```

## Usage
```bash
python zagruz.py
```
1. Paste supported video URL in the input field
2. Select download directory (default: current folder)
3. Click "Download" or press Enter to start
4. Monitor progress in the log window
5. Use "Interrupt" button to cancel ongoing downloads

## Build from Source
```bash
git clone https://github.com/yourusername/zagruz.git
cd zagruz
python -m pip install -r requirements.txt
```

## Dependencies
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download backend (supports 1000+ sites)

## License
![AGPLv3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
