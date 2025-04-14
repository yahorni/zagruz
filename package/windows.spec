# vim: ft=python

from importlib.metadata import version

from PyInstaller.utils.hooks import collect_data_files

pkg_version = version('zagruz')

a = Analysis(
    ['../src/zagruz/zagruz.py'],

    datas=[
        *collect_data_files('yt_dlp'),
        ('../src/zagruz/translations/*.qm', 'translations'),
        ('../assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        'yt_dlp.compat',
        'yt_dlp.downloader',
        'yt_dlp.extractor',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ]
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='zagruz-win.exe',
    upx=True,
    console=False,
    icon='../assets/icon.ico',
)
