import numpy as np
import librosa
from scipy import signal
import soundfile as sf
import torch
from scipy.signal import fftconvolve

class MotorTonalDSP:
    def __init__(self, target_sr=48000):
        """
        Inicializa el motor DSP. 
        Fijamos la frecuencia de muestreo a 48 kHz por exigencia del hardware comercial.
        """
        self.target_sr = target_sr

    def cargar_audio(self, ruta_archivo):
        try:
            senal, sr = librosa.load(ruta_archivo, sr=self.target_sr, mono=True)
            return senal, sr
        except Exception as e:
            raise ValueError(f"Error topológico al procesar la matriz de audio: {e}")

    def inferencia_neuronal_nam(self, ruta_modelo_nam, senal_di):
        """
        Motor de inferencia axiomático para NAM v0.12.2.
        Parsea explícitamente el archivo .nam (JSON) a un diccionario en RAM.
        """
        import torch
        import numpy as np
        import json
        
        # El puntero correcto confirmado en tu topología local
        from nam.models import init_from_nam
        
        try:
            # 1. Parseo Estructural: Un archivo .nam es un contenedor JSON
            # Lo decodificamos a un diccionario de Python para evitar el error de 'str'
            with open(ruta_modelo_nam, 'r', encoding='utf-8') as archivo:
                configuracion_matricial = json.load(archivo)
                
            # 2. Instanciación Neuronal
            # init_from_nam exige el diccionario de hiperparámetros y pesos
            modelo = init_from_nam(configuracion_matricial)
            modelo.eval()
            
            # 3. Vectorización de la Señal (Transformación a Tensor Float32)
            tensor_in = torch.tensor(senal_di, dtype=torch.float32)
            if tensor_in.ndim == 1:
                tensor_in = tensor_in.unsqueeze(0)  # [Batch=1, Muestras=N]
                
            # 4. Inferencia No Lineal (Sin cómputo de gradientes)
            with torch.no_grad():
                output = modelo(tensor_in)
                
            # 5. Extracción y Normalización de Salida
            if isinstance(output, dict) and "audio" in output:
                resultado = output["audio"].detach().cpu().numpy()
            elif isinstance(output, (list, tuple)):
                resultado = output[0].detach().cpu().numpy()
            else:
                resultado = output.detach().cpu().numpy()
                
            return resultado.flatten()
            
        except json.JSONDecodeError:
            raise RuntimeError(f"El archivo {ruta_modelo_nam} no tiene un formato JSON válido o está corrupto.")
        except Exception as e:
            raise RuntimeError(f"Colapso en la propagación de la matriz NAM: {str(e)}")

    def calcular_factor_cresta(self, senal, umbral_db=-40):
        pico_maximo = np.max(np.abs(senal))
        umbral_lineal = 10 ** (umbral_db / 20)
        senal_activa = senal[np.abs(senal) > umbral_lineal]
        if len(senal_activa) == 0:
            return 0.0
        rms_activo = np.sqrt(np.mean(senal_activa**2))
        return 20 * np.log10(pico_maximo / rms_activo)

    def calcular_cruces_cero(self, senal):
        return np.mean(librosa.zero_crossings(senal, pad=False))
    
    def calcular_psd_welch(self, senal, nperseg=4096):
        frecuencias, psd = signal.welch(senal, fs=self.target_sr, nperseg=nperseg)
        psd_db = 10 * np.log10(psd + 1e-10)
        return frecuencias, psd_db
    
    def calcular_mse_espectral(self, psd_objetivo, psd_fuente):
        """
        Calcula el Error Cuadrático Medio (MSE) entre dos espectros.
        Aplica una normalización de media nula (Zero-Mean) para aislar la 
        topología de ecualización pura y descartar el offset de amplitud escalar.
        """
        if len(psd_objetivo) != len(psd_fuente):
            raise ValueError(f"Discrepancia dimensional: Objetivo ({len(psd_objetivo)}) vs Fuente ({len(psd_fuente)}).")
            
        # 1. Normalización Topológica (Alineación de Energía)
        # Forzamos que el promedio de energía de ambas curvas sea 0 dB relativo
        psd_obj_norm = psd_objetivo - np.mean(psd_objetivo)
        psd_fnt_norm = psd_fuente - np.mean(psd_fuente)
        
        # 2. Cálculo Estricto del Error Topológico
        mse = np.mean((psd_obj_norm - psd_fnt_norm)**2)
        # Inyectar esto para ver los datos exactos en la terminal
        print(f"DEBUG - Energía Objetivo: {np.mean(psd_objetivo):.2f} dB, Energía Fuente: {np.mean(psd_fuente):.2f} dB")
        return mse
    
    def sintetizar_filtro_fir(self, psd_objetivo, psd_fuente, muestras_salida=2048):
        H_mag = 10 ** ((psd_objetivo - psd_fuente) / 20.0)
        cepstrum = np.fft.irfft(np.log(H_mag + 1e-10))
        n = len(cepstrum)
        ventana = np.zeros(n)
        ventana[0], ventana[1:n//2], ventana[n//2] = 1.0, 2.0, 1.0
        ir_tiempo = np.fft.irfft(np.exp(np.fft.rfft(cepstrum * ventana)))
        ir_hardware = ir_tiempo[:muestras_salida]
        pico = np.max(np.abs(ir_hardware))
        if pico > 0:
            ir_hardware = (ir_hardware / pico) * (10 ** (-0.1 / 20))
        return ir_hardware
        
    def exportar_ir(self, vector_ir, nombre_archivo="IR_Clonado_DSP.wav", target_sr_export=None):
        sr_final = target_sr_export if target_sr_export else self.target_sr
        if sr_final != self.target_sr:
            vector_ir = librosa.resample(vector_ir, orig_sr=self.target_sr, target_sr=sr_final)
        sf.write(nombre_archivo, vector_ir, sr_final, subtype='PCM_24')
        
    def cargar_ir_referencia(self, ruta_ir):
        """
        Carga un archivo de impulso de respuesta (IR) y lo normaliza.
        Extrae el vector acústico que servirá como constante de gabinete.
        """
        import librosa
        import numpy as np
        try:
            vector_ir, _ = librosa.load(ruta_ir, sr=self.target_sr, mono=True)
            # Normalización del vector para evitar saturación post-convolución
            pico = np.max(np.abs(vector_ir))
            if pico > 0:
                vector_ir = vector_ir / pico
            return vector_ir
        except Exception as e:
            raise ValueError(f"Fallo al cargar el IR de referencia: {e}")

    def aplicar_gabinete_referencia(self, senal_amp, vector_ir_ref):
        """
        Aplica el Teorema de Convolución utilizando la Transformada Rápida de Fourier (FFT).
        Complejidad algorítmica reducida para latencia mínima.
        """
        # mode='same' recorta matemáticamente las colas para mantener la longitud de la señal DI
        senal_final = fftconvolve(senal_amp, vector_ir_ref, mode='same')
        return senal_final

# --- BLOQUE DE VALIDACIÓN ---
if __name__ == "__main__":
    motor = MotorTonalDSP()
    print(f"Motor DSP verificado a {motor.target_sr} Hz.")