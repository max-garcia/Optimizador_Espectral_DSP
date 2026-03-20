# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# =====================================================================
# AXIOMA DE RECOLECCIÓN WINDOWS: IA & DSP
# =====================================================================
# Capturamos DLLs de Torch y metadatos de Demucs
demucs_datas = collect_data_files('demucs')
torchcodec_binaries = collect_dynamic_libs('torchcodec')

block_cipher = None

a = Analysis(
    ['interfaz_gui.py'],
    pathex=[],
    binaries=torchcodec_binaries,
    datas=[
        ('logo_tgn.png', '.'), 
    ] + demucs_datas,
    hiddenimports=[
        'librosa', 'soundfile', 'torch', 'torchaudio', 'demucs', 'nam',
        'scipy.signal', 'scipy.ndimage', 'matplotlib.backends.backend_tkagg',
        'numpy', 'scipy', 'unittest', 'torchcodec'
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
    name='TGN_Tone_Architect_v1.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Cambia a True si necesitas ver la consola de errores al probar
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo_tgn.ico'], # En Windows usa formato .ico
)