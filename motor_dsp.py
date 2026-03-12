import numpy as np
import librosa
from scipy import signal
import soundfile as sf
import torch

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
        Ejecuta la inferencia NAM v0.12.2.
        Utiliza el cargador de la clase base con resolución de ruta absoluta
        para evitar errores de indexación de metadatos.
        """
        import torch
        import numpy as np
        import os
        from nam.models.base import BaseNet
        
        try:
            # 1. Normalización de la ruta de la matriz
            # Forzamos la ruta absoluta para que el cargador interno no se confunda
            ruta_abs = os.path.abspath(ruta_modelo_nam)
            
            # 2. Carga del grafo neuronal
            # En v0.12.2, BaseNet es la clase madre. Si .load falla, 
            # usamos .load_base que es el método de bajo nivel.
            try:
                modelo = BaseNet.load(ruta_abs)
            except AttributeError:
                modelo = BaseNet.load_base(ruta_abs)
                
            modelo.eval()
            
            # 3. Preparación del Tensor DI [1, Samples]
            tensor_in = torch.tensor(senal_di, dtype=torch.float32)
            if tensor_in.ndim == 1:
                tensor_in = tensor_in.unsqueeze(0)
            
            # 4. Inferencia Forward
            with torch.no_grad():
                output = modelo(tensor_in)
                
            # 5. Extracción y limpieza de la matriz de salida
            if isinstance(output, dict):
                resultado = output["audio"].detach().cpu().numpy()
            elif isinstance(output, (list, tuple)):
                resultado = output[0].detach().cpu().numpy()
            else:
                resultado = output.detach().cpu().numpy()
                
            return resultado.flatten()
            
        except Exception as e:
            raise RuntimeError(f"Error estructural en NAM: {str(e)}")

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
        if len(psd_objetivo) != len(psd_fuente):
            raise ValueError(f"Discrepancia dimensional: Objetivo ({len(psd_objetivo)}) vs Fuente ({len(psd_fuente)}).")
        return np.mean((psd_objetivo - psd_fuente)**2)
    
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

# --- BLOQUE DE VALIDACIÓN ---
if __name__ == "__main__":
    motor = MotorTonalDSP()
    print(f"Motor DSP verificado a {motor.target_sr} Hz.")