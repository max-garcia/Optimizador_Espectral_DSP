# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# AXIOMA: Recolección de datos y binarios dinámicos de IA (Demucs + Torch)
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
    [],
    exclude_binaries=True,
    name='TGN_Tone_Architect_v1.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64', # Optimizado para tu Mac Mini M1/M2/M3
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo_tgn.icns'], # Asegúrate de tener el icono o cámbialo a .png si no tienes .icns
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TGN Tone Architect.app',
)

app = BUNDLE(
    coll,
    name='TGN Tone Architect.app',
    icon='logo_tgn.icns',
    bundle_identifier='com.theguitarnotebook.tonearchitect',
)