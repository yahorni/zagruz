# vim: ft=python

import os
import sys
from importlib.metadata import version

from PyInstaller.utils.hooks import collect_data_files

pkg_version = version('zagruz')


# configure qt plugins to decrease final binary size
pyqt6_plugins_dir = os.path.join(
    os.path.dirname(sys.executable),
    'lib/python3.13/site-packages/PyQt6/Qt6/plugins'
)
qt_plugins = []
platforms_dir = os.path.join(pyqt6_plugins_dir, 'platforms')
if os.path.exists(platforms_dir):
    qt_plugins.append((platforms_dir, 'PyQt6/Qt6/plugins/platforms'))

a = Analysis(
    ['../src/zagruz/zagruz.py'],

    binaries=qt_plugins,
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
    ]
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='zagruz-linux-' + pkg_version,
    upx=True,
    console=False,
    disable_windowed_tracker=True,
)
