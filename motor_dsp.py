import numpy as np
import librosa
from scipy import signal
import soundfile as sf
import torch
from scipy.signal import fftconvolve, resample_poly

# =====================================================================
# AXIOMAS DE SEPARACIÓN NEURONAL (Estructuras de Control Asíncrono)
# =====================================================================
from enum import Enum
from dataclasses import dataclass
import warnings
import subprocess
import threading
import re
import sys
import os
from typing import Callable, Optional
from collections import deque

class ComputeDevice(Enum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"

class TargetStem(Enum):
    ALL = "all"        
    OTHER = "other"    # Aísla la pista objetivo (ej. guitarra/instrumento)
    GUITAR = "guitar"

class QualityLevel(Enum):
    # Matriz paramétrica: (Etiqueta UI, Shifts, Overlap)
    DRAFT = ("Básico", 1, 0.10)
    STANDARD = ("Estándar", 2, 0.25)
    PRO = ("Pro", 5, 0.50)

    def __init__(self, label: str, shifts: int, overlap: float):
        self.label = label
        self.shifts = shifts
        self.overlap = overlap

@dataclass
class DemucsInferenceConfig:
    device: ComputeDevice
    quality: QualityLevel
    stem: TargetStem

    def __post_init__(self):
        self._validate_compute_limits()

    def _validate_compute_limits(self):
        # Restricción computacional: Evita colapso por tiempo asintótico en CPU
        if self.device == ComputeDevice.CPU and self.quality == QualityLevel.PRO:
            warnings.warn(
                "Inferencia en CPU con nivel PRO detectada. "
                "Degradando tensor a nivel ESTÁNDAR para evitar el bloqueo del hilo.",
                RuntimeWarning
            )
            self.quality = QualityLevel.STANDARD

    def get_demucs_args(self) -> list:
        # Vector de argumentos estrictos para la red HTDemucs
        args = [
            "-n", "htdemucs_6s",
            "-d", self.device.value,
            "--shifts", str(self.quality.shifts),
            "--overlap", str(self.quality.overlap),
            "--float32"
        ]
        
        # Mapeo del tensor objetivo
        if self.stem == TargetStem.OTHER:
            args.extend(["--two-stems", "other"])
        elif self.stem == TargetStem.GUITAR:
            args.extend(["--two-stems", "guitar"])
            
        return args

class DemucsRunner:
    """
    Controlador asíncrono. Aísla la carga I/O y de CPU/GPU del hilo principal.
    """
    def __init__(self, config: DemucsInferenceConfig, input_path: str, output_dir: str):
        self.config = config
        self.input_path = input_path
        self.output_dir = output_dir
        self._process: Optional[subprocess.Popen] = None
        self._is_running = False

    def start_extraction(self, 
                         on_progress: Callable[[float], None], 
                         on_complete: Callable[[int], None], 
                         on_error: Callable[[str], None]):
        
        if self._is_running:
            return 

        self._is_running = True
        worker_thread = threading.Thread(
            target=self._run_subprocess,
            args=(on_progress, on_complete, on_error),
            daemon=True 
        )
        worker_thread.start()

    def _run_subprocess(self, on_progress, on_complete, on_error):
        import sys
        import subprocess
        import re
        from collections import deque

        # Forzamos el uso del motor Python del entorno virtual
        cmd = [sys.executable, "-m", "demucs.separate", self.input_path, "-o", self.output_dir]
        cmd.extend(self.config.get_demucs_args())
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1, 
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            progress_pattern = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
            
            # Matriz de memoria circular (LIFO espacial) para retener el Traceback real
            log_buffer = deque(maxlen=15)

            for line in self._process.stdout:
                linea_limpia = line.strip()
                if linea_limpia:
                    log_buffer.append(linea_limpia) # Guardamos el axioma temporal
                
                match = progress_pattern.search(line)
                if match:
                    percent_val = float(match.group(1))
                    on_progress(percent_val)

            self._process.wait()
            return_code = self._process.returncode
            self._is_running = False

            if return_code == 0:
                on_complete(return_code)
            else:
                # Extracción del colapso exacto
                traza_error = "\n".join(log_buffer)
                on_error(f"Fallo del subproceso (Código {return_code}).\n\nTraza de la Terminal:\n{traza_error}")

        except Exception as e:
            self._is_running = False
            on_error(str(e))

    def terminate(self):
        if self._process and self._is_running:
            self._process.terminate()
            self._is_running = False


# =====================================================================
# MOTOR TONAL DSP (Cálculo LTI y Filtros FIR)
# =====================================================================
class MotorTonalDSP:
    def __init__(self, target_sr=48000):
        """
        Inicializa el motor DSP. 
        Fijamos la frecuencia de muestreo a 48 kHz por exigencia del hardware comercial.
        """
        self.target_sr = target_sr

    def cargar_audio(self, ruta_archivo):
        try:
            # CAMBIO: Guardamos sr en self.target_sr (o self.fs_origen) 
            # para que persista en el objeto
            senal, sr = librosa.load(ruta_archivo, sr=self.target_sr, mono=True)
            self.fs_origen = sr # <--- AÑADE ESTA LÍNEA
            return senal, sr
        except Exception as e:
            raise ValueError(f"Error topológico al procesar la matriz de audio: {e}")
    def alinear_fase_correlacion(self, senal_obj, senal_fnt):
        """
        Alineación Temporal LTI Híbrida (Entera + Sub-muestral).
        Resuelve la discrepancia de fase micrométrica calculando el vértice parabólico
        de la correlación y aplicando un filtro Sinc para desplazamientos fraccionales.
        """
        correlacion = signal.correlate(senal_obj, senal_fnt, mode="full", method="fft")
        lags = np.arange(-len(senal_fnt) + 1, len(senal_obj))
        idx_pico = np.argmax(np.abs(correlacion))
        lag_entero = lags[idx_pico]
        
        # Interpolación Parabólica (Axioma de Smith)
        if 0 < idx_pico < len(correlacion) - 1:
            y_m1 = np.abs(correlacion[idx_pico - 1])
            y_0 = np.abs(correlacion[idx_pico])
            y_p1 = np.abs(correlacion[idx_pico + 1])
            
            denominador = y_m1 - 2 * y_0 + y_p1
            if denominador != 0:
                delta = 0.5 * (y_m1 - y_p1) / denominador
            else:
                delta = 0.0
        else:
            delta = 0.0
            
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
        
        # Compensación Sub-muestral (Filtro Sinc)
        fnt_sync_frac = self.retraso_fraccional_sinc(fnt_sync, delta)
        
        return obj_sync, fnt_sync_frac

    def retraso_fraccional_sinc(self, senal, retraso_fraccional, longitud_filtro=32):
        if np.abs(retraso_fraccional) < 1e-5:
            return senal
            
        n = np.arange(-longitud_filtro, longitud_filtro + 1)
        filtro_sinc = np.sinc(n - retraso_fraccional)
        ventana = np.blackman(2 * longitud_filtro + 1)
        filtro_sinc = filtro_sinc * ventana
        filtro_sinc /= np.sum(filtro_sinc)
        
        senal_desplazada = fftconvolve(senal, filtro_sinc, mode='same')
        return senal_desplazada

    def alinear_energia_rms(self, senal_obj, senal_fnt):
        rms_obj = np.sqrt(np.mean(senal_obj**2))
        rms_fnt = np.sqrt(np.mean(senal_fnt**2))
        
        if rms_fnt < 1e-12:
            return senal_fnt
            
        factor_escala = rms_obj / rms_fnt
        return senal_fnt * factor_escala

    def inferencia_neuronal_nam(self, ruta_modelo_nam, senal_di):
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
        if np.max(np.abs(senal)) < 1e-7:
            return np.linspace(0, self.target_sr//2, nperseg//2 + 1), np.full(nperseg//2 + 1, 1e-12)

        frecuencias, psd = signal.welch(senal, fs=self.target_sr, nperseg=nperseg)
        psd = np.maximum(psd, 1e-12)
        return frecuencias, psd

    def calcular_mse_espectral(self, psd_objetivo, psd_fuente):
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
        from scipy.ndimage import gaussian_filter1d

        idx_validos = frecuencias > 20.0
        f_validas = frecuencias[idx_validos]
        p_validos = psd[idx_validos]

        log_f = np.log2(f_validas)
        log_p = 10 * np.log10(np.maximum(p_validos, 1e-12))

        log_f_uniforme = np.linspace(log_f[0], log_f[-1], len(f_validas) * 2)
        log_p_interp = np.interp(log_f_uniforme, log_f, log_p)

        sigma = (ancho_banda * len(log_f_uniforme)) / (log_f[-1] - log_f[0])
        log_p_suave = gaussian_filter1d(log_p_interp, sigma=sigma)

        p_suave_db = np.interp(log_f, log_f_uniforme, log_p_suave)
        p_suave_lineal = 10 ** (p_suave_db / 10.0)

        psd_final = np.full(len(frecuencias), 1e-12)
        psd_final[idx_validos] = p_suave_lineal

        return psd_final

    def sintetizar_filtro_fir(self, frecuencias, psd_objetivo, psd_fuente, muestras_salida=2048):
        muestras_salida = int(muestras_salida)
        
        env_obj = self.extraer_envolvente_logaritmica(frecuencias, psd_objetivo, ancho_banda=0.33)
        env_fnt = self.extraer_envolvente_logaritmica(frecuencias, psd_fuente, ancho_banda=0.33)
        
        H_mag = np.sqrt(env_obj / (env_fnt + 1e-12))
        H_mag = np.clip(H_mag, 0.01, 100.0) 
        
        cepstrum_fir = np.fft.irfft(np.log(H_mag + 1e-12))
        n = len(cepstrum_fir)
        ventana = np.zeros(n)
        ventana[0] = 1.0
        ventana[1:n//2] = 2.0
        ventana[n//2] = 1.0
        
        ir_tiempo = np.fft.irfft(np.exp(np.fft.rfft(cepstrum_fir * ventana)))
        ir_hardware = np.copy(ir_tiempo[:muestras_salida])
        
        longitud_fade = int(muestras_salida * 0.1)
        ventana_fade = np.linspace(1.0, 0.0, longitud_fade)
        ir_hardware[-longitud_fade:] = ir_hardware[-longitud_fade:] * ventana_fade
        
        pico = np.max(np.abs(ir_hardware))
        if pico > 0:
            ir_hardware = (ir_hardware / pico) * (10 ** (-0.1 / 20.0))
            
        return np.nan_to_num(ir_hardware)

    def exportar_ir(self, vector_ir, nombre_archivo="IR_Clonado_DSP.wav", target_sr_export=None):
        sr_final = int(target_sr_export if target_sr_export else self.target_sr)
        sr_origen = int(self.target_sr)
        
        if sr_final != sr_origen:
            vector_ir = resample_poly(vector_ir, up=sr_final, down=sr_origen)
            
        vector_ir = np.nan_to_num(vector_ir)
        sf.write(nombre_archivo, vector_ir, sr_final, subtype='PCM_24')

    def cargar_ir_referencia(self, ruta_ir):
        try:
            vector_ir, _ = librosa.load(ruta_ir, sr=self.target_sr, mono=True)
            pico = np.max(np.abs(vector_ir))
            if pico > 0:
                vector_ir = vector_ir / pico
            return vector_ir
        except Exception as e:
            raise ValueError(f"Fallo al cargar el IR de referencia: {e}")

    def aplicar_gabinete_referencia(self, senal_amp, vector_ir_ref):
        senal_final = fftconvolve(senal_amp, vector_ir_ref, mode='same')
        return senal_final