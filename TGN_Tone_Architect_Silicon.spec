# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['interfaz_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('TGN_DSP_Engine.dylib', '.'), ('/Users/max_garcia/Optimizador_Espectral_DSP/venv_universal/lib/python3.12/site-packages/demucs/remote', 'demucs/remote')],
    hiddenimports=['demucs.separate', 'demucs.pretrained'],
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
    [],
    exclude_binaries=True,
    name='TGN_Tone_Architect_Silicon',
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
    icon=['logo_tgn.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TGN_Tone_Architect_Silicon',
)
app = BUNDLE(
    coll,
    name='TGN_Tone_Architect_Silicon.app',
    icon='logo_tgn.icns',
    bundle_identifier=None,
)
