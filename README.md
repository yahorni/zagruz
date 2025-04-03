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

## Usage

```bash
git clone https://github.com/yahorni/zagruz.git
cd zagruz
make
```

## Build and install

```bash
# install dependencies
make init

# run application
make run        # using make
uv run zagruz   # using uv

# build python package
make build

# build packaged executable (pyinstaller)
make package

# clean all build artifacts
make clean
```

## Dependencies

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download backend (supports 1000+ sites)

## TODO

- [x] Binary package for linux/windows
- [x] Implement CI/CD pipeline with GitHub Actions
- [ ] Update button to update the app and ffmpeg dependency
- [ ] Preconfigured profiles of yt-dlp ("best", "tv", "audio",...)
- [ ] Russian language support
- [ ] Configurable download format
- [ ] Progress bar instead of `[download]` log spamming
- [ ] Download directory persistence between sessions
- [ ] Add automated tests for download interruption/resumption
- [ ] Add dark/light theme toggle

## License

![AGPLv3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
