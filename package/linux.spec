# vim: ft=python

from importlib.metadata import version

from PyInstaller.building.build_main import EXE, PYZ, Analysis
from PyInstaller.utils.hooks import collect_data_files

pkg_version = version('zagruz')

a = Analysis(
    ['../src/zagruz/zagruz.py'],
    datas=[
        *collect_data_files('yt_dlp'),
        ('../src/zagruz/translations/*.qm', 'translations')
    ],
    hiddenimports=[
        'yt_dlp.compat',
        'yt_dlp.downloader',
        'yt_dlp.extractor',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'qdarktheme'
    ]
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=f'zagruz-linux-{pkg_version}',
    upx=True,
    console=False,
    disable_windowed_tracker=True,
)
