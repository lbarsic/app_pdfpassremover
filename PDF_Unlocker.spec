# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter
from PyInstaller.utils.hooks import collect_all

# Same .ico CustomTkinter applies to the window title bar, so the
# downloaded .exe file matches the running app's header icon.
CTK_ICON = os.path.join(
    os.path.dirname(customtkinter.__file__),
    "assets", "icons", "CustomTkinter_icon_Windows.ico",
)
if not os.path.isfile(CTK_ICON):
    raise SystemExit(f"CustomTkinter window icon not found: {CTK_ICON}")

datas = []
binaries = []
hiddenimports = ['pikepdf._qpdf']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['unlock_pdf.py'],
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
    name='PDF_Unlocker',
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
    icon=CTK_ICON,
)
