# config_dmg.py
import os

# 1. Definición del Volumen
volume_name = 'Optimizador Espectral DSP'
format = 'UDZO' # Formato de compresión estricto de Apple (zlib)

# 2. Inyección del binario
# Apunta al archivo .app que PyInstaller generó en la Fase 4
files = ['dist/Optimizador_Espectral_DSP.app']

# 3. Enrutamiento del Enlace Simbólico
symlinks = {'Applications': '/Applications'}

# 4. Geometría Visual de la Ventana del Instalador
# ((x_pantalla, y_pantalla), (ancho, alto))
window_rect = ((200, 200), (600, 400))
icon_size = 128

# 5. Coordenadas Cartesianas de los Íconos dentro del contenedor
icon_locations = {
    'Optimizador_Espectral_DSP.app': (140, 120),
    'Applications': (460, 120)
}