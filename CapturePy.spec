# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('tools', 'tools')]
binaries = []
hiddenimports = ['PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.sip', 'mss.windows', 'win32gui', 'win32con', 'win32api', 'pywintypes', 'keyboard', 'PIL', 'PIL.Image', 'PIL.ImageFile']
tmp_ret = collect_all('cv2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('comtypes')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'PyQt6.QtQuick', 'PyQt6.QtQml', 'PyQt6.QtDesigner', 'PyQt6.QtWebEngine', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'PyQt6.QtMultimedia', 'PyQt6.QtBluetooth', 'PyQt6.QtLocation'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CapturePy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CapturePy',
)
