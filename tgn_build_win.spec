# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['interfaz_gui.py'],
    pathex=[],
    binaries=[],
    datas=[ 
        ('logo_tgn.png', '.'),
        ('icono_app.ico', '.'), 
    ],
    hiddenimports=[
        'librosa', 'soundfile', 'torch', 'torchaudio', 'demucs', 'nam',
        'scipy.signal', 'scipy.ndimage', 'matplotlib.backends.backend_tkagg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest'],
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
    console=False, # Sin ventana de comandos negra
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icono_app.ico' # Icono para el .exe
)