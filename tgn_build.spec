# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['interfaz_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logo_tgn.png', '.'),
        ('icono_app.icns', '.'), # Inyectamos el recurso en la raíz del paquete
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
    [],
    exclude_binaries=True,
    name='TGN_Tone_Architect_Bin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TGN Tone Architect',
)

app = BUNDLE(
    coll,
    name='TGN Tone Architect.app',
    icon='icono_app.icns', # <--- PUNTO CRÍTICO 1: Nombre exacto del archivo
    bundle_identifier='com.theguitarnotebook.tonearchitect',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSUIElement': 'False',
        'CFBundleIconFile': 'icono_app.icns', # <--- PUNTO CRÍTICO 2: Registro en el Info.plist
    },
)
