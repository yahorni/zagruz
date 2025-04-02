# vim: ft=python

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['../zagruz.py'],  # Path relative to spec file location
    pathex=[],
    binaries=[],
    datas=collect_data_files('yt_dlp'),
    hiddenimports=[
        'yt_dlp.compat',
        'yt_dlp.downloader',
        'yt_dlp.extractor',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'dbus'  # Required for Linux desktop integration
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='zagruz-linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Better for Linux terminal integration
    disable_windowed_tracker=True,
    # icon='../assets/icon.png',
)
