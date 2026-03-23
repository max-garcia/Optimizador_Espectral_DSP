import sys
from setuptools import setup

# AXIOMA DE ESTABILIDAD:
# Elevamos el límite de recursión para el mapeo de grafos complejos
sys.setrecursionlimit(15000)

APP = ['interfaz_gui.py']
DATA_FILES = [('', ['TGN_DSP_Engine.dylib'])]

OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': "TGN Tone Architect",
        'CFBundleDisplayName': "TGN Tone Architect",
        'CFBundleIdentifier': "com.tgn.tonearchitect",
        'CFBundleVersion': "1.5.0",
        'CFBundleShortVersionString': "1.5.0",
        'LSMinimumSystemVersion': '12.0.0',
    },
    # 1. INCLUSIÓN EXPLÍCITA: Forzamos la carga de los núcleos UI y DSP
    'packages': ['numpy', 'scipy', 'matplotlib', 'customtkinter', 'PIL'],
    
    # 2. EXCLUSIÓN TOPOLÓGICA (La cura para tu error):
    # Prohibimos que modulegraph intente seguir rastros de otros empaquetadores
    # o librerías de Linux (X11/GI) que confunden a Python 3.13.
    'excludes': [
        'PyInstaller', 
        'gi', 
        'tkinter.tix', 
        'PIL.ImageQt', 
        'PIL.ImageTk'
    ],
    
    'arch': 'universal2', # Axioma de compatibilidad total Intel/Silicon
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)