# zagruz - yt-dlp GUI Wrapper

![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux-lightgrey)

A cross-platform GUI frontend for yt-dlp featuring:

- **Presets**: TV (480p MP4), Audio (320kbps MP3), Best Quality
- **Theme Support**: System/Light/Dark modes with DPI scaling
- **Localization**: English & Russian interface
- **Update System**: Built-in FFmpeg updater

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

## Development

```bash
# run dev
make clean init run

# run wheel
make clean init build run-wheel

# run package
make clean init package run-package
```

## Dependencies

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download backend (supports 1000+ sites)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [PyQtDarkTheme](https://github.com/5yutan5/PyQtDarkTheme/) - Qt app theme

## TODO

- [x] Binary package for linux/windows
- [x] Implement CI/CD pipeline with GitHub Actions
- [x] Preconfigured profiles of yt-dlp ("best", "tv", "audio",...)
- [x] "Options" button + window
  - [x] Add dark/light theme toggle
  - [x] Download directory selection
  - [x] Russian language support
- [x] Configuration file (QSettings)
  - [x] Selected theme
  - [x] Selected language
  - [x] Download directory persistence between sessions
- [ ] Ffmpeg integration
  - [x] Manual updater
  - [ ] Startup validation
  - [ ] Hot-reload without restart
- [ ] Update system
  - [ ] Application updates via GitHub
  - [ ] Change log display
- [ ] Quality-of-life improvements
  - [ ] Progress bar visualization
  - [ ] Preset customization
- [ ] Automated testing for download interruption/resumption

## License

![AGPLv3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
