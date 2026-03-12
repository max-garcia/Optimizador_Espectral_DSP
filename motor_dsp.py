import numpy as np
import librosa
from scipy import signal
import soundfile as sf

class MotorTonalDSP:
    def __init__(self, target_sr=48000):
        """
        Inicializa el motor DSP. 
        Fijamos la frecuencia de muestreo a 48 kHz por exigencia del hardware comercial.
        """
        self.target_sr = target_sr

    def cargar_audio(self, ruta_archivo):
        """
        Ingesta el archivo de audio. Si es estéreo, colapsa la matriz a mono.
        Si la frecuencia de muestreo difiere, ejecuta un remuestreo analítico.
        """
        try:
            # librosa.load extrae la serie de tiempo como un array unidimensional (vector) de NumPy
            senal, sr = librosa.load(ruta_archivo, sr=self.target_sr, mono=True)
            return senal, sr
        except Exception as e:
            raise ValueError(f"Error topológico al procesar la matriz de audio: {e}")

    def calcular_factor_cresta(self, senal, umbral_db=-40):
        """
        Calcula el Factor de Cresta (Crest Factor) purgando los silencios.
        Aplica una máscara booleana para calcular el RMS estrictamente sobre 
        la señal activa, evitando anomalías por pausas en la pista.
        """
        pico_maximo = np.max(np.abs(senal))
        
        # Convertir el umbral logarítmico a amplitud lineal
        umbral_lineal = 10 ** (umbral_db / 20)
        
        # Máscara de tensores: aísla las muestras que superan el umbral
        senal_activa = senal[np.abs(senal) > umbral_lineal]
        
        # Prevención de error topológico por divisiones nulas
        if len(senal_activa) == 0:
            return 0.0
            
        # Cálculo estricto sobre la señal purgada
        rms_activo = np.sqrt(np.mean(senal_activa**2))
        
        factor_cresta_db = 20 * np.log10(pico_maximo / rms_activo)
        return factor_cresta_db

    def calcular_cruces_cero(self, senal):
        """
        Calcula la Tasa de Cruces por Cero (ZCR - Zero-Crossing Rate).
        Mide la densidad frecuencial (qué tan "brillante" o distorsionada es la señal).
        """
        cruces = librosa.zero_crossings(senal, pad=False)
        tasa_zcr = np.mean(cruces)
        return tasa_zcr
    
    def calcular_psd_welch(self, senal, nperseg=4096):
        """
        Calcula la Densidad Espectral de Potencia (PSD) mediante el método de Welch.
        Divide la señal en segmentos superpuestos y promedia sus periodogramas
        para aislar la curva de ecualización pura del hardware.
        """
        # nperseg=4096 a 48kHz otorga una resolución de bin frecuencial de ~11.7 Hz.
        # signal.welch aplica automáticamente una ventana de Hanning para mitigar la fuga espectral.
        frecuencias, psd = signal.welch(senal, fs=self.target_sr, nperseg=nperseg)
        
        # Transformación de la magnitud de potencia a escala logarítmica (Decibelios).
        # Sumamos un infinitesimal (1e-10) para evitar el colapso algebraico de log(0).
        psd_db = 10 * np.log10(psd + 1e-10)
        
        return frecuencias, psd_db
    
    def calcular_mse_espectral(self, psd_objetivo, psd_fuente):
        """
        Calcula el Error Cuadrático Medio (MSE) entre dos espectros.
        Verifica axiomáticamente que ambos vectores tengan la misma 
        dimensión topológica antes de ejecutar la resta escalar.
        """
        if len(psd_objetivo) != len(psd_fuente):
            raise ValueError(f"Discrepancia dimensional: Objetivo ({len(psd_objetivo)}) vs Fuente ({len(psd_fuente)}).")
            
        mse = np.mean((psd_objetivo - psd_fuente)**2)
        return mse
    
    def sintetizar_filtro_fir(self, psd_objetivo, psd_fuente, muestras_salida=2048):
        """
        Sintetiza un filtro FIR de Fase Mínima mediante análisis Cepstral.
        Garantiza latencia cero en sistemas integrados (Line 6, Fractal, Kemper).
        """
        # 1. Función de Transferencia (Resta logarítmica)
        diff_db = psd_objetivo - psd_fuente
        
        # 2. Conversión de Decibelios a Magnitud Lineal
        H_mag = 10 ** (diff_db / 20.0)
        
        # 3. Paso al dominio Cepstral
        log_mag = np.log(H_mag + 1e-10)
        cepstrum = np.fft.irfft(log_mag)
        n = len(cepstrum)
        
        # 4. Ventana Causal (Fuerza la energía de la señal al t=0)
        ventana_causal = np.zeros(n)
        ventana_causal[0] = 1.0          # Impulso original
        ventana_causal[1:n//2] = 2.0     # Duplicación de fase positiva
        if n % 2 == 0:
            ventana_causal[n//2] = 1.0   # Frecuencia de Nyquist intacta
            
        cepstrum_min_fase = cepstrum * ventana_causal
        
        # 5. Retorno al dominio espectral complejo y aplicación de la Exponencial
        espectro_complejo = np.exp(np.fft.rfft(cepstrum_min_fase))
        
        # 6. Transformada Inversa final (Dominio del Tiempo)
        ir_tiempo = np.fft.irfft(espectro_complejo)
        
        # 7. Truncamiento estricto a los requisitos del hardware (1024 o 2048 muestras)
        ir_hardware = ir_tiempo[:muestras_salida]
        
        # 8. Normalización a -0.1 dB para evitar recortes (clipping) en la pedalera
        pico = np.max(np.abs(ir_hardware))
        if pico > 0:
            ir_hardware = (ir_hardware / pico) * (10 ** (-0.1 / 20))
            
        return ir_hardware
        
    def exportar_ir(self, vector_ir, nombre_archivo="IR_Clonado_DSP.wav", target_sr_export=None):
        """
        Escribe la matriz unidimensional en un archivo de audio PCM de 24-bit.
        Inyecta un remuestreo analítico si el hardware (ej. Kemper) exige una base de tiempo distinta.
        """
        sr_final = target_sr_export if target_sr_export else self.target_sr
        
        # Si el hardware destino exige 44.1 kHz, aplicamos un remuestreo de alta calidad
        if sr_final != self.target_sr:
            vector_ir = librosa.resample(vector_ir, orig_sr=self.target_sr, target_sr=sr_final)
            
        # El formato 'PCM_24' garantiza la resolución que exige la industria
        sf.write(nombre_archivo, vector_ir, sr_final, subtype='PCM_24')

# --- BLOQUE DE VALIDACIÓN ESTOCÁSTICA ---
# Este bloque solo se ejecuta si corremos este archivo directamente en la terminal,
# no se ejecutará cuando la interfaz gráfica importe esta clase en el futuro.

if __name__ == "__main__":
    motor = MotorTonalDSP()
    print(f"Motor DSP inicializado a {motor.target_sr} Hz.")
    
    # Asegúrate de colocar las rutas de tus dos audios
    ruta_disco = "/Users/mariadelrosariotello/Optimizador_Espectral_DSP/audio_prueba.wav" 
    ruta_pod = "/Users/mariadelrosariotello/Optimizador_Espectral_DSP/audio_prueba2.wav" 
    
    try:
        senal_obj, _ = motor.cargar_audio(ruta_disco)
        senal_fnt, _ = motor.cargar_audio(ruta_pod)
        
        _, psd_obj = motor.calcular_psd_welch(senal_obj)
        _, psd_fnt = motor.calcular_psd_welch(senal_fnt)
        
        print("\n--- INICIANDO SÍNTESIS MULTI-HARDWARE ---")
        
        # 1. LINE 6 (POD Go / Helix) -> 1024 muestras, 48 kHz
        ir_line6 = motor.sintetizar_filtro_fir(psd_obj, psd_fnt, muestras_salida=1024)
        motor.exportar_ir(ir_line6, "ToneMatch_Line6_1024.wav")
        print("✓ Matriz Line 6 compilada (1024 samples, 48 kHz)")

        # 2. FRACTAL AUDIO (Axe-Fx) -> 2048 muestras, 48 kHz
        ir_fractal = motor.sintetizar_filtro_fir(psd_obj, psd_fnt, muestras_salida=2048)
        motor.exportar_ir(ir_fractal, "ToneMatch_Fractal_2048.wav")
        print("✓ Matriz Fractal compilada (2048 samples, 48 kHz)")

        # 3. KEMPER PROFILER -> 2048 muestras, 44.1 kHz (Remuestreo)
        ir_kemper = motor.sintetizar_filtro_fir(psd_obj, psd_fnt, muestras_salida=2048)
        motor.exportar_ir(ir_kemper, "ToneMatch_Kemper_44100.wav", target_sr_export=44100)
        print("✓ Matriz Kemper compilada (2048 samples, downsampled a 44.1 kHz)")
        
        print("\n--- EXPORTACIÓN COMPLETADA CON ÉXITO ---")
        
    except Exception as e:
        print(f"Colapso en la síntesis: {e}")