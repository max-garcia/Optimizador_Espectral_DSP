import numpy as np
import librosa
from scipy import signal
import soundfile as sf
import torch
from scipy.signal import fftconvolve, resample_poly

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

    def alinear_fase_correlacion(self, senal_obj, senal_fnt):
        """
        Alineación temporal matemática mediante Correlación Cruzada Rápida.
        Resuelve el error humano en el recorte de audio encontrando el Lag perfecto.
        """
        import numpy as np
        from scipy import signal
        
        # 1. Ejecución del Teorema de Correlación Cruzada (FFT para máxima velocidad)
        correlacion = signal.correlate(senal_obj, senal_fnt, mode="full", method="fft")
        lags = np.arange(-len(senal_fnt) + 1, len(senal_obj))
        
        # 2. Extracción del vector de retardo (Tau)
        lag_optimo = lags[np.argmax(np.abs(correlacion))]
        
        # 3. Sincronización Topológica de los Tensores
        if lag_optimo > 0:
            # La señal objetivo está adelantada respecto a la fuente
            obj_sync = senal_obj[lag_optimo:]
            fnt_sync = senal_fnt[:len(obj_sync)]
        elif lag_optimo < 0:
            # La señal fuente está adelantada respecto al objetivo
            lag_abs = abs(lag_optimo)
            fnt_sync = senal_fnt[lag_abs:]
            obj_sync = senal_obj[:len(fnt_sync)]
        else:
            obj_sync = senal_obj
            fnt_sync = senal_fnt
            
        # 4. Truncamiento al Mínimo Común (Evita desbordes de RAM)
        min_len = min(len(obj_sync), len(fnt_sync))
        
        print(f"DEBUG DSP - Compensación de fase aplicada: {lag_optimo} muestras.")
        return obj_sync[:min_len], fnt_sync[:min_len]

    def alinear_energia_rms(self, senal_obj, senal_fnt):
        import numpy as np
        rms_obj = np.sqrt(np.mean(senal_obj**2))
        rms_fnt = np.sqrt(np.mean(senal_fnt**2))
        
        if rms_fnt < 1e-12:
            return senal_fnt
            
        factor_escala = rms_obj / rms_fnt
        return senal_fnt * factor_escala

    def inferencia_neuronal_nam(self, ruta_modelo_nam, senal_di):
        import torch
        import json
        from nam.models import init_from_nam
        
        try:
            with open(ruta_modelo_nam, 'r', encoding='utf-8') as archivo:
                configuracion_matricial = json.load(archivo)
                
            modelo = init_from_nam(configuracion_matricial)
            modelo.eval()
            
            tensor_in = torch.tensor(senal_di, dtype=torch.float32)
            if tensor_in.ndim == 1:
                tensor_in = tensor_in.unsqueeze(0)
                
            with torch.no_grad():
                output = modelo(tensor_in)
                
            if isinstance(output, dict) and "audio" in output:
                resultado = output["audio"].detach().cpu().numpy()
            elif isinstance(output, (list, tuple)):
                resultado = output[0].detach().cpu().numpy()
            else:
                resultado = output.detach().cpu().numpy()
                
            return resultado.flatten()
            
        except json.JSONDecodeError:
            raise RuntimeError(f"El archivo {ruta_modelo_nam} está corrupto.")
        except Exception as e:
            raise RuntimeError(f"Colapso en matriz NAM: {str(e)}")

    def calcular_psd_welch(self, senal, nperseg=4096):
        import numpy as np
        from scipy import signal
        
        if np.max(np.abs(senal)) < 1e-7:
            return np.linspace(0, self.target_sr//2, nperseg//2 + 1), np.full(nperseg//2 + 1, 1e-12)

        frecuencias, psd = signal.welch(senal, fs=self.target_sr, nperseg=nperseg)
        psd = np.maximum(psd, 1e-12)
        return frecuencias, psd

    def calcular_mse_espectral(self, psd_objetivo, psd_fuente):
        import numpy as np
        if len(psd_objetivo) != len(psd_fuente):
            raise ValueError("Discrepancia dimensional.")

        db_obj = 10 * np.log10(psd_objetivo)
        db_fnt = 10 * np.log10(psd_fuente)

        std_obj = np.std(db_obj)
        std_fnt = np.std(db_fnt)
        
        psd_obj_norm = (db_obj - np.mean(db_obj)) / (std_obj if std_obj > 0 else 1.0)
        psd_fnt_norm = (db_fnt - np.mean(db_fnt)) / (std_fnt if std_fnt > 0 else 1.0)

        mse = np.mean((psd_obj_norm - psd_fnt_norm)**2)
        return mse

    def suavizar_espectro_fraccional(self, frecuencias, psd, fraccion_octava=6.0):
        """
        Filtro logarítmico fraccional. El estándar Audio Engineering Society (AES).
        Conserva resolución en graves y plancha resonancias en agudos.
        """
        import numpy as np
        psd_suavizado = np.copy(psd)
        psd_suavizado = np.maximum(np.nan_to_num(psd_suavizado, nan=1e-12), 1e-12)
        
        # Factor Q basado en 1/N octavas
        factor_bw = (2**(1.0 / (2.0 * fraccion_octava)) - 2**(-1.0 / (2.0 * fraccion_octava)))
        
        for i, fc in enumerate(frecuencias):
            if fc < 20.0: # Ignorar ruido sub-sónico
                continue
                
            bw = fc * factor_bw
            f_min = fc - bw/2.0
            f_max = fc + bw/2.0
            
            idx_min = np.searchsorted(frecuencias, f_min)
            idx_max = np.searchsorted(frecuencias, f_max)
            
            if idx_max > idx_min:
                psd_suavizado[i] = np.mean(psd[idx_min:idx_max])
                
        return psd_suavizado
    
    def sintetizar_filtro_fir(self, frecuencias, psd_objetivo, psd_fuente, muestras_salida=2048):
        import numpy as np
        
        # 1. Purga espectral: Suavizado psicoacústico logarítmico (1/6 Octava)
        psd_obj_limpio = self.suavizar_espectro_fraccional(frecuencias, psd_objetivo, fraccion_octava=6.0)
        psd_fnt_limpia = self.suavizar_espectro_fraccional(frecuencias, psd_fuente, fraccion_octava=6.0)
        
        # 2. Magnitud del Filtro (Axioma LTI)
        H_mag = np.sqrt(psd_obj_limpio / (psd_fnt_limpia + 1e-12))
        
        # 3. Transformada Homomórfica (Reconstrucción de Fase Mínima)
        cepstrum = np.fft.irfft(np.log(H_mag + 1e-12))
        n = len(cepstrum)
        ventana = np.zeros(n)
        ventana[0], ventana[1:n//2], ventana[n//2] = 1.0, 2.0, 1.0
        
        # 4. Síntesis temporal
        ir_tiempo = np.fft.irfft(np.exp(np.fft.rfft(cepstrum * ventana)))
        ir_hardware = ir_tiempo[:muestras_salida]
        
        # 5. Mitigación del Fenómeno de Gibbs
        longitud_fade = int(muestras_salida * 0.1)
        ventana_fade = np.linspace(1.0, 0.0, longitud_fade)
        ir_hardware[-longitud_fade:] = ir_hardware[-longitud_fade:] * ventana_fade
        
        # 6. Normalización estricta a -0.1 dBTP
        pico = np.max(np.abs(ir_hardware))
        if pico > 0:
            ir_hardware = (ir_hardware / pico) * (10 ** (-0.1 / 20.0))
            
        return ir_hardware
        
    def exportar_ir(self, vector_ir, nombre_archivo="IR_Clonado_DSP.wav", target_sr_export=None):
        """
        Remuestreo Polifásico estricto para hardware.
        Evita el pre-ringing destructivo del transitorio.
        """
        from scipy.signal import resample_poly
        import soundfile as sf
        
        sr_final = target_sr_export if target_sr_export else self.target_sr
        
        if sr_final != self.target_sr:
            # Interpolación estricta usando filtro FIR pasabajos integrado
            vector_ir = resample_poly(vector_ir, up=sr_final, down=self.target_sr)
            
        sf.write(nombre_archivo, vector_ir, sr_final, subtype='PCM_24')

    def cargar_ir_referencia(self, ruta_ir):
        import librosa
        import numpy as np
        try:
            vector_ir, _ = librosa.load(ruta_ir, sr=self.target_sr, mono=True)
            pico = np.max(np.abs(vector_ir))
            if pico > 0:
                vector_ir = vector_ir / pico
            return vector_ir
        except Exception as e:
            raise ValueError(f"Fallo al cargar el IR de referencia: {e}")

    def aplicar_gabinete_referencia(self, senal_amp, vector_ir_ref):
        from scipy.signal import fftconvolve
        senal_final = fftconvolve(senal_amp, vector_ir_ref, mode='same')
        return senal_final

# --- BLOQUE DE VALIDACIÓN ---
if __name__ == "__main__":
    motor = MotorTonalDSP()
    print(f"Motor DSP verificado a {motor.target_sr} Hz.")