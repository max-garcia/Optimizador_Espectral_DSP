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
        Alineación Temporal LTI Híbrida (Entera + Sub-muestral).
        Resuelve la discrepancia de fase micrométrica calculando el vértice parabólico
        de la correlación y aplicando un filtro Sinc para desplazamientos fraccionales.
        """
        import numpy as np
        from scipy import signal
        
        # 1. Correlación Cruzada Discreta (Lag Entero)
        correlacion = signal.correlate(senal_obj, senal_fnt, mode="full", method="fft")
        lags = np.arange(-len(senal_fnt) + 1, len(senal_obj))
        idx_pico = np.argmax(np.abs(correlacion))
        lag_entero = lags[idx_pico]
        
        # 2. Interpolación Parabólica (Axioma de Smith) para Lag Fraccional
        if 0 < idx_pico < len(correlacion) - 1:
            y_m1 = np.abs(correlacion[idx_pico - 1])
            y_0 = np.abs(correlacion[idx_pico])
            y_p1 = np.abs(correlacion[idx_pico + 1])
            
            # Vértice exacto de la parábola
            denominador = y_m1 - 2 * y_0 + y_p1
            if denominador != 0:
                delta = 0.5 * (y_m1 - y_p1) / denominador
            else:
                delta = 0.0
        else:
            delta = 0.0
            
        # 3. Alineación Discreta Básica (Corte de tensores)
        if lag_entero > 0:
            obj_sync = senal_obj[lag_entero:]
            fnt_sync = senal_fnt[:len(obj_sync)]
        elif lag_entero < 0:
            lag_abs = abs(lag_entero)
            fnt_sync = senal_fnt[lag_abs:]
            obj_sync = senal_obj[:len(fnt_sync)]
        else:
            obj_sync = senal_obj
            fnt_sync = senal_fnt
            
        min_len = min(len(obj_sync), len(fnt_sync))
        obj_sync = obj_sync[:min_len]
        fnt_sync = fnt_sync[:min_len]
        
        # 4. Compensación Sub-muestral (Filtro Sinc)
        fnt_sync_frac = self.retraso_fraccional_sinc(fnt_sync, delta)
        
        return obj_sync, fnt_sync_frac

    def retraso_fraccional_sinc(self, senal, retraso_fraccional, longitud_filtro=32):
        """
        Síntesis de Filtro FIR Pasa-todo para el desplazamiento temporal sub-muestral.
        Utiliza el Teorema de Whittaker-Shannon con ventana de Blackman para mitigar el error de truncamiento.
        """
        import numpy as np
        from scipy.signal import fftconvolve
        
        if np.abs(retraso_fraccional) < 1e-5:
            return senal
            
        n = np.arange(-longitud_filtro, longitud_filtro + 1)
        
        # Función Sinc continua desplazada por la fracción micrométrica
        filtro_sinc = np.sinc(n - retraso_fraccional)
        
        # Inyección de ventana geométrica (Blackman)
        ventana = np.blackman(2 * longitud_filtro + 1)
        filtro_sinc = filtro_sinc * ventana
        
        # Normalización de ganancia unitaria (Evita colapso de amplitud)
        filtro_sinc /= np.sum(filtro_sinc)
        
        # Convolución LTI para ejecutar el desplazamiento en el dominio del tiempo
        senal_desplazada = fftconvolve(senal, filtro_sinc, mode='same')
        
        return senal_desplazada

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

    def extraer_envolvente_logaritmica(self, frecuencias, psd, ancho_banda=0.33):
        """
        Axioma de Suavizado Psicoacústico (Log-Domain Smoothing).
        Transforma el eje a escala logarítmica, aplica un filtro gaussiano (1/3 de octava)
        para difuminar la matriz armónica de las notas, y retorna la EQ pura del equipo.
        """
        import numpy as np
        from scipy.ndimage import gaussian_filter1d

        # 1. Ignorar el vector DC (0 Hz) para prevenir el colapso de log(0)
        idx_validos = frecuencias > 20.0
        f_validas = frecuencias[idx_validos]
        p_validos = psd[idx_validos]

        # 2. Transformación al dominio logarítmico (Octavas y Decibeles)
        log_f = np.log2(f_validas)
        log_p = 10 * np.log10(np.maximum(p_validos, 1e-12))

        # 3. Interpolación Lineal a Grilla Uniforme
        # Necesario porque la salida de Welch es lineal en Hz, no en octavas.
        log_f_uniforme = np.linspace(log_f[0], log_f[-1], len(f_validas) * 2)
        log_p_interp = np.interp(log_f_uniforme, log_f, log_p)

        # 4. Difuminado Gaussiano Estricto (Desenfoque de notas)
        # ancho_banda = 0.33 corresponde a 1/3 de Octava (Estándar AES)
        sigma = (ancho_banda * len(log_f_uniforme)) / (log_f[-1] - log_f[0])
        log_p_suave = gaussian_filter1d(log_p_interp, sigma=sigma)

        # 5. Retorno al dominio lineal matricial
        p_suave_db = np.interp(log_f, log_f_uniforme, log_p_suave)
        p_suave_lineal = 10 ** (p_suave_db / 10.0)

        # 6. Reconstrucción del Tensor Completo (Inyectando el piso sub-sónico)
        psd_final = np.full(len(frecuencias), 1e-12)
        psd_final[idx_validos] = p_suave_lineal

        return psd_final

    def sintetizar_filtro_fir(self, frecuencias, psd_objetivo, psd_fuente, muestras_salida=2048):
        import numpy as np
        muestras_salida = int(muestras_salida)
        
        # 1. Extracción Estricta de la Envolvente (Desenfoque de cuerdas)
        env_obj = self.extraer_envolvente_logaritmica(frecuencias, psd_objetivo, ancho_banda=0.33)
        env_fnt = self.extraer_envolvente_logaritmica(frecuencias, psd_fuente, ancho_banda=0.33)
        
        # 2. Magnitud del Filtro LTI Macro
        H_mag = np.sqrt(env_obj / (env_fnt + 1e-12))
        H_mag = np.clip(H_mag, 0.01, 100.0) # Límite estricto +/- 40dB
        
        # 3. Transformada Homomórfica (Reconstrucción de Fase Mínima real)
        cepstrum_fir = np.fft.irfft(np.log(H_mag + 1e-12))
        n = len(cepstrum_fir)
        ventana = np.zeros(n)
        ventana[0] = 1.0
        ventana[1:n//2] = 2.0
        ventana[n//2] = 1.0
        
        # 4. Síntesis temporal del Impulso
        ir_tiempo = np.fft.irfft(np.exp(np.fft.rfft(cepstrum_fir * ventana)))
        ir_hardware = np.copy(ir_tiempo[:muestras_salida])
        
        # 5. Mitigación del Fenómeno de Gibbs (Fundido de salida)
        longitud_fade = int(muestras_salida * 0.1)
        ventana_fade = np.linspace(1.0, 0.0, longitud_fade)
        ir_hardware[-longitud_fade:] = ir_hardware[-longitud_fade:] * ventana_fade
        
        # 6. Normalización estricta a -0.1 dBTP
        pico = np.max(np.abs(ir_hardware))
        if pico > 0:
            ir_hardware = (ir_hardware / pico) * (10 ** (-0.1 / 20.0))
            
        return np.nan_to_num(ir_hardware)

    def exportar_ir(self, vector_ir, nombre_archivo="IR_Clonado_DSP.wav", target_sr_export=None):
        from scipy.signal import resample_poly
        import soundfile as sf
        import numpy as np
        
        sr_final = int(target_sr_export if target_sr_export else self.target_sr)
        sr_origen = int(self.target_sr)
        
        if sr_final != sr_origen:
            vector_ir = resample_poly(vector_ir, up=sr_final, down=sr_origen)
            
        vector_ir = np.nan_to_num(vector_ir)
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
    
    def aislar_tensor_guitarra(self, ruta_mezcla, directorio_salida):
        """
        Axioma de Separación de Fuentes Estocásticas (STFT).
        Utiliza la red neuronal Demucs (htdemucs_6s) aislando estrictamente la guitarra.
        """
        import subprocess
        import os
        
# Axioma de Inferencia de Alta Fidelidad:
        # Se inyecta overlap al 80% y 2 pasadas estocásticas (shifts) para promediar errores de fase.
        comando = [
            "demucs", 
            "-n", "htdemucs_6s",
            "--two-stems=guitar",
            "--float32",
            "--overlap", "0.8",
            "--shifts", "2",
            ruta_mezcla,
            "-o", directorio_salida
        ]
        
        try:
            # Ejecución bloqueante del subproceso neuronal
            proceso = subprocess.run(comando, capture_output=True, text=True, check=True)
            
            # Reconstrucción de la ruta de salida determinista dictada por Demucs
            nombre_base = os.path.splitext(os.path.basename(ruta_mezcla))[0]
            ruta_guitarra_aislada = os.path.join(directorio_salida, "htdemucs_6s", nombre_base, "guitar.wav")
            
            if os.path.exists(ruta_guitarra_aislada):
                return ruta_guitarra_aislada
            else:
                raise FileNotFoundError("La red neuronal finalizó, pero la matriz 'guitar.wav' no fue sintetizada.")
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Colapso en la inferencia de Demucs:\n{e.stderr}")