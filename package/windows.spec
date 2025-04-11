# vim: ft=python

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['../src/zagruz/zagruz.py'],
    pathex=[],
    binaries=[],
    datas=[
        *collect_data_files('yt_dlp'),
        ('../src/zagruz/translations/*.qm', 'translations')
    ],
    hiddenimports=[
        'yt_dlp.compat',
        'yt_dlp.downloader',
        'yt_dlp.extractor',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='zagruz.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_tracker=False,
    # icon='../assets/icon.ico',
)
