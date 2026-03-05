# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\projectsss\\smile-tool\\M2CIDSmile-Tool\\python-gui\\app_icon.ico', '.'), ('C:\\Users\\siddh\\AppData\\Roaming\\Python\\Python314\\site-packages\\customtkinter', 'customtkinter'), ('C:\\Users\\siddh\\AppData\\Roaming\\Python\\Python314\\site-packages\\certifi', 'certifi')]
binaries = []
hiddenimports = ['customtkinter', 'darkdetect', 'certifi', 'packaging', 'packaging.version', 'packaging.specifiers', 'packaging.requirements']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('certifi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['m2cidsmile_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='M2CIDSmile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\projectsss\\smile-tool\\M2CIDSmile-Tool\\python-gui\\app_icon.ico'],
)
