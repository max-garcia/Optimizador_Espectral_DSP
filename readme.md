# TGN Tone Architect (v1.4)
### Engine for Neural Audio Matching & Spectral Optimization

**TGN Tone Architect** es un ecosistema de procesamiento digital de señales (DSP) diseñado para la captura y recreación de timbres de amplificación de alta fidelidad. Utiliza inferencia neuronal (NAM) y convolución de respuesta al impulso (IR) para encontrar la combinación óptima de hardware modelado mediante análisis de error cuadrático medio (MSE) en el dominio de la frecuencia.

---

## 🔬 Rigor Matemático y Motor DSP

A diferencia de los matchers convencionales, este software opera bajo el **Axioma de Invarianza Espectral**. El motor de búsqueda ha sido optimizado para procesar señales asimétricas (diferentes longitudes de audio) sin colapsar la coherencia de fase.

### 1. Estimación de Densidad Espectral (PSD)
Utilizamos el **Método de Welch** para transformar las señales del dominio del tiempo al dominio de la frecuencia:
- **Ventana de Hann:** Para reducir el leakage espectral en las discontinuidades de la señal.
- **Invarianza Temporal:** El algoritmo promedia la energía RMS, permitiendo comparar un "stem" completo (objetivo) contra un riff corto (entrada DI) sin sesgo estadístico.

### 2. Función de Costo (Criterio de Selección)
La selección del amplificador y el gabinete ganador se rige por la minimización del **Error Cuadrático Medio Espectral (SMSE)**:

$$MSE = \frac{1}{n} \sum_{i=1}^{n} (P_{target}(f_i) - P_{model}(f_i))^2$$

Donde $P(f)$ es la densidad de potencia espectral normalizada. El sistema busca el mínimo global en una matriz combinatoria de $N$ modelos NAM y $M$ respuestas al impulso.

---

## Características Premium

* **Matriz Combinatoria:** Prueba automática de múltiples modelos `.nam` contra bancos de IRs `.wav`.
* **Alineación Energética Automática:** Normalización basada en RMS para comparaciones auditivas y matemáticas justas.
* **Visualización en Tiempo Real:** Renderizado de curvas de respuesta de frecuencia comparadas mediante Matplotlib.
* **Arquitectura Asíncrona:** Ejecución de inferencia neuronal en hilos separados para mantener la fluidez de la interfaz (Tkinter).

---

## Instalación y Uso (macOS)

El software se distribuye como una imagen de disco (.dmg) monolítica que incluye todas las dependencias (PyTorch, Librosa, SciPy).

1. Descarga `TGN_Tone_Architect_v1.4.dmg`.
2. Arrastra la aplicación a tu carpeta de **Applications**.
3. **Primer inicio:** Debido a las políticas de seguridad de macOS, haz clic derecho (Control + Clic) sobre la App y selecciona **Abrir**.

---

## Estructura del Proyecto

* `interfaz_gui.py`: Lógica de la UI y gestión de estados de la matriz.
* `motor_dsp.py`: Núcleo matemático, inferencia NAM y cálculos de PSD.
* `tgn_build.spec`: Matriz de compilación para PyInstaller.
* `icono_app.icns`: Identidad visual de la suite.

---

## Desarrollado por:
**Max García** - *The Guitar Notebook*
*Formación: Matemática Pura*

> "Sin datos exactos y justificables, el tono es solo una opinión. Aquí, el tono es una variable optimizada."