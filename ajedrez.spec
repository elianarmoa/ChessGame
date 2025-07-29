# -*- mode: python ; coding: utf-8 -*-
import os

# Asegura que la carpeta 'images' existe
datas = [('images/' + f, 'images') for f in os.listdir('images') if os.path.isfile('images/' + f)]

a = Analysis(
    ['ajedrez.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.datas,   # <- Correcto
    [],
    name='ajedrez',
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
)
