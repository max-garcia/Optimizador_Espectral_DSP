import tkinter as tk
import os
import sys
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import requests
from PIL import Image, ImageTk
import urllib.request
import subprocess
import time
import numpy as np
import librosa
import soundfile as sf
import gc

# Importación estricta del núcleo matemático
from motor_dsp import MotorTonalDSP
from gestor_licencias import CriptografiaHWID  

def resolver_ruta(ruta_relativa):
    try:
        ruta_base = sys._MEIPASS
    except Exception:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, ruta_relativa)

class OptimizadorGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("TGN Tone Architect - The Guitar Notebook")
        self.root.geometry("1000x750") 
        self.fs_origen = 44100
        
        self.motor = MotorTonalDSP()
        self.seguridad = CriptografiaHWID()

        self.construir_barra_menu()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.tab_nam = ttk.Frame(self.notebook)
        self.tab_hardware = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_nam, text="Rama A: Búsqueda Correlacional (NAM)")
        self.notebook.add(self.tab_hardware, text="Rama B: Síntesis Hardware (Filtros FIR)")

        self.frame_grafico = None

        self.construir_rama_nam()
        self.construir_rama_hardware()
        self.construir_lienzo_espectral()
        self.construir_firma_ingenieria()

    def construir_barra_menu(self):
        self.frame_menu_local = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        self.frame_menu_local.pack(side=tk.TOP, fill=tk.X)

        self.btn_menu_sistema = ttk.Menubutton(self.frame_menu_local, text="Sistema")
        self.btn_menu_sistema.pack(side=tk.LEFT, padx=5, pady=2)

        self.menu_desplegable = tk.Menu(self.btn_menu_sistema, tearoff=0)
        self.menu_desplegable.add_command(label="Verificar Actualizaciones", command=self.verificar_actualizacion)
        self.menu_desplegable.add_command(label="Créditos / Acerca de", command=self.mostrar_creditos)
        self.menu_desplegable.add_separator() 
        self.menu_desplegable.add_command(label="Salir", command=self.salir_aplicacion)

        self.btn_menu_sistema["menu"] = self.menu_desplegable

    def construir_rama_nam(self):
        self.frame_master_nam = ttk.Frame(self.tab_nam)
        self.frame_master_nam.pack(expand=True, fill=tk.BOTH)

        frame_controles_nam = ttk.Frame(self.frame_master_nam)
        frame_controles_nam.pack(expand=True, pady=10)

        # Módulo de Inferencia IA para Rama NAM
        frame_obj_nam = ttk.Frame(frame_controles_nam)
        frame_obj_nam.grid(row=0, column=0, padx=15, pady=5)
        
        self.btn_cargar_obj_nam = ttk.Button(frame_obj_nam, text="1A. Objetivo Aislado (.wav)", width=35, command=lambda: self.cargar_archivo("Objetivo_NAM"))
        self.btn_cargar_obj_nam.pack(pady=(0, 5))

        frame_ia_params_nam = ttk.Frame(frame_obj_nam)
        frame_ia_params_nam.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_ia_params_nam, text="Motor:", font=('SF Pro Display', 10)).grid(row=0, column=0, sticky=tk.W)
        self.var_demucs_hw_nam = tk.StringVar(value="cpu")
        ttk.Combobox(frame_ia_params_nam, textvariable=self.var_demucs_hw_nam, values=("cpu", "cuda"), state="readonly", width=8).grid(row=0, column=1, padx=5)

        ttk.Label(frame_ia_params_nam, text="Calidad:", font=('SF Pro Display', 10)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.var_demucs_calidad_nam = tk.StringVar(value="Estándar")
        ttk.Combobox(frame_ia_params_nam, textvariable=self.var_demucs_calidad_nam, values=("Básico", "Estándar", "Pro"), state="readonly", width=8).grid(row=1, column=1, padx=5)

        self.btn_extraer_ia_nam = ttk.Button(frame_obj_nam, text="1B. Extraer de Mezcla (IA)", width=35, command=lambda: self.aislar_hilo_extraccion_ia(rama="NAM"))
        self.btn_extraer_ia_nam.pack()

        # Controles Estándar NAM
        self.btn_cargar_di_nam = ttk.Button(frame_controles_nam, text="2. Tono DI Limpio (.wav)", width=30, command=lambda: self.cargar_archivo("DI_NAM"))
        self.btn_cargar_di_nam.grid(row=0, column=1, padx=15, pady=5, sticky=tk.N)

        self.btn_cargar_dir_nam = ttk.Button(frame_controles_nam, text="3. Carpeta Cabezales (.nam)", width=30, command=self.seleccionar_directorio_nam)
        self.btn_cargar_dir_nam.grid(row=1, column=0, padx=15, pady=5)

        self.btn_cargar_dir_ir = ttk.Button(frame_controles_nam, text="4. Carpeta Gabinetes IR (.wav)", width=30, command=self.seleccionar_directorio_ir)
        self.btn_cargar_dir_ir.grid(row=1, column=1, padx=15, pady=5)

        self.var_tolerancia = tk.StringVar()
        self.selector_tolerancia = ttk.Combobox(frame_controles_nam, textvariable=self.var_tolerancia, state="readonly", width=45, justify='center')
        self.selector_tolerancia['values'] = ("Perfección Topológica (MSE < 5.0)", "Aceptable Comercial (MSE < 15.0)", "Aproximación (MSE < 30.0)")
        self.selector_tolerancia.current(1)
        self.selector_tolerancia.grid(row=2, column=0, columnspan=2, pady=10)

        self.btn_buscar_nam = ttk.Button(frame_controles_nam, text="Ejecutar Matriz Combinatoria", width=40, command=self.aislar_hilo_busqueda_nam)
        self.btn_buscar_nam.grid(row=3, column=0, columnspan=2, pady=10)

        self.frame_progreso_nam = ttk.Frame(frame_controles_nam)
        self.frame_progreso_nam.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        self.barra_progreso_nam = ttk.Progressbar(self.frame_progreso_nam, orient="horizontal", mode="determinate")
        self.barra_progreso_nam.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 5))
        
        self.lbl_porcentaje_nam = ttk.Label(self.frame_progreso_nam, text="0%", font=('Times New Roman', 12, 'bold'))
        self.lbl_porcentaje_nam.pack(side=tk.RIGHT, padx=(0, 15))

        self.lbl_resultado_nam = ttk.Label(frame_controles_nam, text="Estado: Esperando tensores...", font=('SF Pro Display', 12, 'bold'), justify='center')
        self.lbl_resultado_nam.grid(row=5, column=0, columnspan=2, pady=5)

    def construir_rama_hardware(self):
        self.frame_master_hw = ttk.Frame(self.tab_hardware)
        self.frame_master_hw.pack(expand=True, fill=tk.BOTH)

        frame_controles = ttk.Frame(self.frame_master_hw)
        frame_controles.pack(expand=True, pady=10)

        # Inyección de la topología neuronal Demucs
        frame_obj = ttk.Frame(frame_controles)
        frame_obj.grid(row=0, column=0, padx=15, pady=10)
        
        self.btn_cargar_obj = ttk.Button(frame_obj, text="1A. Inyectar Objetivo Aislado (.wav)", width=35, command=lambda: self.cargar_archivo("Objetivo"))
        self.btn_cargar_obj.pack(pady=(0, 5))
        
        frame_ia_params = ttk.Frame(frame_obj)
        frame_ia_params.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_ia_params, text="Motor:", font=('SF Pro Display', 10)).grid(row=0, column=0, sticky=tk.W)
        self.var_demucs_hw = tk.StringVar(value="cpu")
        ttk.Combobox(frame_ia_params, textvariable=self.var_demucs_hw, values=("cpu", "cuda"), state="readonly", width=8).grid(row=0, column=1, padx=5)

        ttk.Label(frame_ia_params, text="Calidad:", font=('SF Pro Display', 10)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.var_demucs_calidad = tk.StringVar(value="Estándar")
        ttk.Combobox(frame_ia_params, textvariable=self.var_demucs_calidad, values=("Básico", "Estándar", "Pro"), state="readonly", width=8).grid(row=1, column=1, padx=5)

        self.btn_extraer_ia = ttk.Button(frame_obj, text="1B. Extraer de Mezcla Completa (IA)", width=35, command=lambda: self.aislar_hilo_extraccion_ia(rama="HW"))
        self.btn_extraer_ia.pack()

        self.btn_cargar_fnt = ttk.Button(frame_controles, text="2. Inyectar Tono Grabado (.wav)", width=30, command=lambda: self.cargar_archivo("Fuente"))
        self.btn_cargar_fnt.grid(row=0, column=1, padx=15, pady=10, sticky=tk.N)

        lbl_ecosistema = ttk.Label(frame_controles, text="3. Ecosistema de Exportación:")
        lbl_ecosistema.grid(row=1, column=0, columnspan=2, pady=(15, 5))
        
        self.variable_hardware = tk.StringVar()
        self.selector_hardware = ttk.Combobox(frame_controles, textvariable=self.variable_hardware, state="readonly", width=55, justify='center')
        self.selector_hardware['values'] = (
            "DAW / PC Plugin (FIR Estándar | 8192 muestras | 48 kHz)",
            "Headrush FX Prime / Core (2048 muestras | 48 kHz)",
            "Fractal Audio Axe-Fx / FM (2048 muestras | 48 kHz)",
            "Fender Tone Master Pro (2048 muestras | 48 kHz)",
            "Kemper Profiler (2048 muestras | 44.1 kHz)",
            "Line 6 Helix / Pod Go (1024 muestras | 48 kHz)",
            "Neural DSP Quad Cortex (1024 muestras | 48 kHz)",
            "IK Multimedia ToneX (1024 muestras | 44.1 kHz)",
            "Nux MG-Series (1024 muestras | 48 kHz)",
            "Zoom G-Series / B-Series (1024 muestras | 44.1 kHz)",
            "Valeton GP / Hotone Ampero (1024 muestras | 44.1 kHz)",
            "Mooer GE / Flamma FX (512 muestras | 44.1 kHz)",
            "Cuvave / M-Vave Cube (512 muestras | 44.1 kHz)"
        )
        self.selector_hardware.current(0)
        self.selector_hardware.grid(row=2, column=0, columnspan=2, pady=5)

        frame_botones_hw = ttk.Frame(frame_controles)
        frame_botones_hw.grid(row=3, column=0, columnspan=2, pady=25)

        self.btn_analizar = ttk.Button(frame_botones_hw, text="Calcular Ecuación Espectral", width=25, command=self.aislar_hilo_analisis)
        self.btn_analizar.pack(side=tk.LEFT, padx=10)

        self.btn_exportar = ttk.Button(frame_botones_hw, text="Sintetizar Filtro FIR", width=25, command=self.aislar_hilo_sintesis)
        self.btn_exportar.pack(side=tk.LEFT, padx=10)
        
        self.frame_progreso_hw = ttk.Frame(frame_controles)
        self.frame_progreso_hw.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        self.barra_progreso_hw = ttk.Progressbar(self.frame_progreso_hw, orient="horizontal", mode="determinate")
        self.barra_progreso_hw.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 5))
        
        self.lbl_porcentaje_hw = ttk.Label(self.frame_progreso_hw, text="0%", font=('Times New Roman', 12, 'bold'))
        self.lbl_porcentaje_hw.pack(side=tk.RIGHT, padx=(0, 15))

    # =========================================================================
    # AXIOMAS NEURONALES UNIFICADOS (Extracción IA)
    # =========================================================================
    def aislar_hilo_extraccion_ia(self, rama="HW"):
        ruta_mezcla = filedialog.askopenfilename(title="Seleccionar Mezcla Comercial", filetypes=[("Archivos de Audio", "*.wav *.mp3 *.flac")])
        if not ruta_mezcla:
            return
            
        advertencia = (
            "La separación neuronal exige rigor computacional.\n\n"
            "El subproceso operará fuera del hilo principal para mantener la GUI fluida.\n"
            "¿Desea inicializar la inferencia IA?"
        )
        
        if messagebox.askokcancel("Carga Computacional", advertencia):
            from motor_dsp import DemucsRunner, DemucsInferenceConfig, ComputeDevice, TargetStem, QualityLevel
            
            directorio_temp = os.path.expanduser("~/TGN_Stem_Cache")
            os.makedirs(directorio_temp, exist_ok=True)
            
            if rama == "NAM":
                self.btn_extraer_ia_nam.config(text="Separando Matriz... (Espere)", state=tk.DISABLED)
                hw_val = self.var_demucs_hw_nam.get()
                calidad_val = self.var_demucs_calidad_nam.get()
                self.barra_progreso_nam['value'] = 0
                self.lbl_porcentaje_nam.config(text="0%")
            else:
                self.btn_extraer_ia.config(text="Separando Matriz... (Espere)", state=tk.DISABLED)
                hw_val = self.var_demucs_hw.get()
                calidad_val = self.var_demucs_calidad.get()
                self.barra_progreso_hw['value'] = 0
                self.lbl_porcentaje_hw.config(text="0%")
            
            mapa_calidad = {
                "Básico": QualityLevel.DRAFT,
                "Estándar": QualityLevel.STANDARD,
                "Pro": QualityLevel.PRO
            }
            hw_seleccionado = ComputeDevice.CUDA if hw_val == "cuda" else ComputeDevice.CPU
            calidad_seleccionada = mapa_calidad.get(calidad_val, QualityLevel.STANDARD)

            config_demucs = DemucsInferenceConfig(
                device=hw_seleccionado,
                quality=calidad_seleccionada,
                stem=TargetStem.GUITAR
            )

            self.runner_ia = DemucsRunner(config=config_demucs, input_path=ruta_mezcla, output_dir=directorio_temp)
            
            self.runner_ia.start_extraction(
                on_progress=lambda p: self.root.after(0, self.actualizar_progreso_ia, p, rama),
                on_complete=lambda code: self.root.after(0, self.finalizar_extraccion_ia, code, directorio_temp, ruta_mezcla, rama),
                on_error=lambda err: self.root.after(0, self.error_extraccion_ia, err, rama)
            )

    def actualizar_progreso_ia(self, valor, rama):
        if rama == "NAM":
            self.barra_progreso_nam['value'] = valor
            self.lbl_porcentaje_nam.config(text=f"{int(valor)}%")
        else:
            self.barra_progreso_hw['value'] = valor
            self.lbl_porcentaje_hw.config(text=f"{int(valor)}%")

    def finalizar_extraccion_ia(self, return_code: int, directorio_temp: str, ruta_mezcla: str, rama: str):
        if return_code != 0:
            self.error_extraccion_ia(f"El hilo secundario abortó con estado: {return_code}", rama)
            return
            
        nombre_base = os.path.splitext(os.path.basename(ruta_mezcla))[0]
        ruta_tensor = os.path.join(directorio_temp, "htdemucs_6s", nombre_base, "guitar.wav")
        
        if os.path.exists(ruta_tensor):
            if rama == "NAM":
                self.ruta_objetivo_nam = ruta_tensor
                self.btn_cargar_obj_nam.config(text="1A. Objetivo Inyectado (Vía IA) ✓")
                self.btn_extraer_ia_nam.config(text="1B. Extraer de Mezcla (IA)", state="normal")
                self.actualizar_progreso_ia(100.0, "NAM")
            else:
                self.ruta_objetivo = ruta_tensor
                self.btn_cargar_obj.config(text="1A. Objetivo Inyectado (Vía IA) ✓")
                self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state="normal")
                self.actualizar_progreso_ia(100.0, "HW")
            
            messagebox.showinfo("Inferencia Exitosa", f"Matriz aislada rigurosamente e inyectada como LTI objetivo.\n\nVector de destino:\n{ruta_tensor}")
        else:
            self.error_extraccion_ia(f"Fallo de E/S estocástico. El tensor no se materializó en:\n{ruta_tensor}", rama)

    def error_extraccion_ia(self, error_msg: str, rama: str):
        if rama == "NAM":
            self.btn_extraer_ia_nam.config(text="1B. Extraer de Mezcla (IA)", state=tk.NORMAL)
        else:
            self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state=tk.NORMAL)
        messagebox.showerror("Colapso Neuronal", f"Fallo en el motor de separación:\n{error_msg}")

    # =========================================================================
    # NÚCLEO LTI Y DSP
    # =========================================================================
    def ejecutar_sintesis_dsp(self, ruta_guardado, seleccion_hw):
        # Matriz Axiomática de Ecosistemas
        mapa_exportacion_hw = {
            "DAW / PC Plugin (FIR Estándar | 8192 muestras | 48 kHz)": {"len": 8192, "sr": 48000, "subtype": "FLOAT"},
            "Headrush FX Prime / Core (2048 muestras | 48 kHz)": {"len": 2048, "sr": 48000, "subtype": "PCM_24"},
            "Fractal Audio Axe-Fx / FM (2048 muestras | 48 kHz)": {"len": 2048, "sr": 48000, "subtype": "PCM_24"},
            "Fender Tone Master Pro (2048 muestras | 48 kHz)": {"len": 2048, "sr": 48000, "subtype": "PCM_24"},
            "Kemper Profiler (2048 muestras | 44.1 kHz)": {"len": 2048, "sr": 44100, "subtype": "PCM_24"},
            "Line 6 Helix / Pod Go (1024 muestras | 48 kHz)": {"len": 1024, "sr": 48000, "subtype": "PCM_24"},
            "Neural DSP Quad Cortex (1024 muestras | 48 kHz)": {"len": 1024, "sr": 48000, "subtype": "PCM_24"},
            "IK Multimedia ToneX (1024 muestras | 44.1 kHz)": {"len": 1024, "sr": 44100, "subtype": "PCM_24"},
            "Nux MG-Series (1024 muestras | 48 kHz)": {"len": 1024, "sr": 48000, "subtype": "PCM_24"},
            "Zoom G-Series / B-Series (1024 muestras | 44.1 kHz)": {"len": 1024, "sr": 44100, "subtype": "PCM_24"},
            "Valeton GP / Hotone Ampero (1024 muestras | 44.1 kHz)": {"len": 1024, "sr": 44100, "subtype": "PCM_24"},
            "Mooer GE / Flamma FX (512 muestras | 44.1 kHz)": {"len": 512, "sr": 44100, "subtype": "PCM_16"},
            "Cuvave / M-Vave Cube (512 muestras | 44.1 kHz)": {"len": 512, "sr": 44100, "subtype": "PCM_16"}
        }

        try:
            perfil = mapa_exportacion_hw.get(seleccion_hw, {"len": 1024, "sr": 48000, "subtype": "PCM_24"})
            muestras = perfil["len"]
            sr_salida = perfil["sr"]
            formato_bits = perfil["subtype"]

            senal_obj, fs_obj = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, fs_fnt = self.motor.cargar_audio(self.ruta_fuente)
            
            # Optimización de tensores
            senal_obj = self.extraer_ventana_max_energia(senal_obj, fs_obj)
            senal_fnt = self.extraer_ventana_max_energia(senal_fnt, fs_fnt)
            
            senal_obj_sync, senal_fnt_sync = self.motor.alinear_fase_correlacion(senal_obj, senal_fnt)
            senal_fnt_alineada = self.motor.alinear_energia_rms(senal_obj_sync, senal_fnt_sync)

            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj_sync)
            _, psd_fnt = self.motor.calcular_psd_welch(senal_fnt_alineada)

            # Genera el FIR con la longitud exacta requerida
            vector_ir = self.motor.sintetizar_filtro_fir(freqs_obj, psd_obj, psd_fnt, muestras_salida=muestras)
            
            # Resampling y Truncamiento riguroso si la frecuencia de origen no coincide
            # Resampling y Truncamiento riguroso
            # CAMBIO: Usamos fs_obj que fue definida arriba al cargar el audio objetivo
            if fs_obj != sr_salida:
                vector_ir = librosa.resample(vector_ir, orig_sr=fs_obj, target_sr=sr_salida)
                
            # Garantizamos que la longitud del vector coincida con el límite del hardware (Axioma de Truncamiento)
            vector_ir = vector_ir[:muestras] 

            # Síntesis Binaria Estricta
            sf.write(ruta_guardado, vector_ir, sr_salida, subtype=formato_bits)

            self.root.after(0, lambda: messagebox.showinfo(
                "Síntesis Exitosa", 
                f"Matriz FIR compilada con precisión topológica.\n\n"
                f"Longitud: {muestras} muestras\n"
                f"Frecuencia Reloj: {sr_salida} Hz\n"
                f"Cuantización: {formato_bits}\n"
                f"Destino: {ruta_guardado}"
            ))
        
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso en Síntesis", err))
        finally:
            self.root.after(0, lambda: self.btn_exportar.config(text="Sintetizar Filtro FIR", state=tk.NORMAL))

    def aislar_hilo_sintesis(self):
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan las matrices de audio.")
            return
        
        try:
            serial_fisico = self.seguridad.extraer_hardware_serial()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_fisico)
            ruta_licencia = self.obtener_ruta_licencia()

            if not os.path.exists(ruta_licencia):
                self.root.after(0, self.mostrar_ventana_activacion)
                return 
                
            with open(ruta_licencia, "r") as archivo:
                if archivo.read().strip() != hash_esperado:
                    messagebox.showerror("Seguridad", "Firma criptográfica inválida.")
                    return
        except Exception as e:
            messagebox.showerror("Seguridad", f"Colapso en lectura de hardware: {e}")
            return

        directorio_escritorio = os.path.expanduser("~/Desktop")
        ruta_guardado = filedialog.asksaveasfilename(
            initialdir=directorio_escritorio,
            defaultextension=".wav", 
            filetypes=[("WAV", "*.wav")]
        )
        
        if not ruta_guardado:
            return
            
        self.btn_exportar.config(text="Sintetizando...", state=tk.DISABLED)
        threading.Thread(target=self.ejecutar_sintesis_dsp, args=(ruta_guardado, self.variable_hardware.get())).start()

    def ejecutar_busqueda_dsp(self):
        import numpy as np
        import os
        import threading
        import gc

        try:
            ruta_obj_local = self.ruta_objetivo_nam
            ruta_di_local = self.ruta_di_nam
            ruta_dir_nam_local = self.ruta_directorio_nam
            ruta_dir_ir_local = getattr(self, 'ruta_directorio_ir', None)
        except AttributeError as e:
            print(f"Error topológico: Faltan variables pre-ejecución ({e})")
            self.root.after(0, lambda: self.btn_buscar_nam.config(text="Ejecutar Matriz Combinatoria", state="normal"))
            return

        try:
            senal_obj, fs_obj = self.motor.cargar_audio(ruta_obj_local)
            senal_di, fs_di = self.motor.cargar_audio(ruta_di_local)

            # --- NUEVO: AXIOMA DE VENTANA DE ALTA ENERGÍA ---
            # Trunca audios largos a los 12 segundos más densos para evitar el colapso de NAM
            def extraer_ventana_max_energia(tensor, fs, segs_max=12):
                muestras_limite = segs_max * fs
                if len(tensor) <= muestras_limite:
                    return tensor
                
                # Escaneo de energía RMS en ventanas de 1 segundo
                paso = fs 
                energias = [np.mean(tensor[i:i+paso]**2) for i in range(0, len(tensor)-paso, paso)]
                idx_pico = np.argmax(energias) * paso
                
                inicio = max(0, idx_pico - (muestras_limite // 2))
                fin = inicio + muestras_limite
                print(f"Tensor optimizado: Recorte de {segs_max}s aplicado por seguridad computacional.")
                return tensor[inicio:fin]

            senal_obj = self.extraer_ventana_max_energia(senal_obj, fs_obj)
            senal_di = self.extraer_ventana_max_energia(senal_di, fs_di)
            # ------------------------------------------------

            archivos_nam = [f for f in os.listdir(ruta_dir_nam_local) if f.endswith('.nam')]
            
            banco_irs = {}
            if ruta_dir_ir_local:
                for arch_ir in [f for f in os.listdir(ruta_dir_ir_local) if f.endswith('.wav')]:
                    banco_irs[arch_ir] = self.motor.cargar_ir_referencia(os.path.join(ruta_dir_ir_local, arch_ir))
            else:
                banco_irs["Bypass_Directo"] = np.array([1.0])

            menor_mse = float('inf')
            amp_ganador = None
            ir_ganador = None
            psd_ganador = None
            freqs_ganador = None
            psd_obj_ganador = None 
            
            total_iteraciones = len(archivos_nam) * len(banco_irs)
            iteracion_actual = 0

            freqs_obj_welch, psd_obj_welch = self.motor.calcular_psd_welch(senal_obj)
            rms_obj = np.sqrt(np.mean(senal_obj**2))

            for nombre_nam in archivos_nam:
                try:
                    senal_amp = self.motor.inferencia_neuronal_nam(os.path.join(ruta_dir_nam_local, nombre_nam), senal_di)

                    if senal_amp is None or np.max(np.abs(senal_amp)) < 1e-6 or np.isnan(senal_amp).any():
                        iteracion_actual += len(banco_irs)
                        continue

                    for nombre_ir, vector_ir in banco_irs.items():
                        senal_final = senal_amp if nombre_ir == "Bypass_Directo" else self.motor.aplicar_gabinete_referencia(senal_amp, vector_ir)
                        
                        rms_fnt = np.sqrt(np.mean(senal_final**2))
                        if rms_fnt > 1e-12:
                            senal_final_alineada = senal_final * (rms_obj / rms_fnt)
                        else:
                            senal_final_alineada = senal_final
                            
                        _, psd_test = self.motor.calcular_psd_welch(senal_final_alineada)
                        
                        if np.isnan(psd_test).any() or np.max(psd_test) < 1e-12:
                            iteracion_actual += 1
                            continue
                            
                        mse_actual = self.motor.calcular_mse_espectral(psd_obj_welch, psd_test)

                        if mse_actual < menor_mse:
                            menor_mse = mse_actual
                            amp_ganador = nombre_nam
                            ir_ganador = nombre_ir
                            psd_ganador = np.copy(psd_test)
                            freqs_ganador = np.copy(freqs_obj_welch)
                            psd_obj_ganador = np.copy(psd_obj_welch) 

                        iteracion_actual += 1
                        progreso = (iteracion_actual / total_iteraciones) * 100
                        self.root.after(0, lambda p=progreso: self.actualizar_progreso_ia(p, "NAM"))
                        
                except Exception as e:
                    print(f"Error estructural procesando {nombre_nam}: {e}")
                    iteracion_actual += len(banco_irs)
                finally:
                    if 'senal_amp' in locals():
                        del senal_amp
                    gc.collect()

            if amp_ganador and psd_ganador is not None and psd_obj_ganador is not None:
                nivel = self.var_tolerancia.get()
                umbral = 5.0 if "Perfección" in nivel else 15.0 if "Aceptable" in nivel else 30.0
                
                if menor_mse <= umbral:
                    texto_final = f"Amplificador (.nam): {amp_ganador}\nIR: {ir_ganador}"
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_final, foreground="#00ffcc"))
                    self.root.after(0, self.renderizar_espectro, freqs_ganador, psd_obj_ganador, freqs_ganador, psd_ganador)
                else:
                    texto_fallo = f"Rechazado. MSE: {menor_mse:.2f}\nSupera el umbral topológico."
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_fallo, foreground="red"))
            else:
                self.root.after(0, lambda: self.lbl_resultado_nam.config(text="Fallo analítico: Matriz evaluada en vacío.", foreground="red"))
                
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Analítico", err))
        finally:
            self.root.after(0, lambda: self.btn_buscar_nam.config(text="Ejecutar Matriz Combinatoria", state="normal"))

    def aislar_hilo_busqueda_nam(self):
        if not hasattr(self, 'ruta_objetivo_nam') or not hasattr(self, 'ruta_di_nam') or not hasattr(self, 'ruta_directorio_nam'):
            messagebox.showerror("Error Topológico", "Faltan variables en la ecuación. Inyecte los tensores requeridos.")
            return

        try:
            serial_fisico = self.seguridad.extraer_hardware_serial()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_fisico)
            ruta_licencia = self.obtener_ruta_licencia()

            if not os.path.exists(ruta_licencia):
                self.root.after(0, self.mostrar_ventana_activacion)
                return 
                
            with open(ruta_licencia, "r") as archivo:
                if archivo.read().strip() != hash_esperado:
                    messagebox.showerror("Seguridad", "Firma criptográfica inválida para esta matriz de silicio.")
                    return
        except Exception as e:
            messagebox.showerror("Seguridad", f"Colapso en lectura de hardware:\n{e}")
            return
        
        self.btn_buscar_nam.config(text="Escaneando... (Espere)", state=tk.DISABLED)
        self.lbl_resultado_nam.config(text="Calculando ...")
        self.barra_progreso_nam['value'] = 0
        self.lbl_porcentaje_nam.config(text="0%")
        
        threading.Thread(target=self.ejecutar_busqueda_dsp).start()

    # =========================================================================
    # OTROS MÉTODOS GUI (Gráficas, Utilidades, Actualizador)
    # =========================================================================
    def cargar_archivo(self, tipo):
        if tipo == "Objetivo_NAM" or tipo == "Objetivo":
            titulo = "Axioma Topológico: Tono Objetivo"
            mensaje = "• Formato: .wav\n• Contiene el Stem (pista aislada) o mezcla a separar."
        elif tipo == "DI_NAM":
            titulo = "ADVERTENCIA ACÚSTICA: Tono DI Limpio"
            mensaje = "El Tono DI debe ser la señal eléctrica virgen.\n✕ Sin amplificador.\n✕ Sin IRs."
        elif tipo == "Fuente":
            titulo = "ADVERTENCIA ACÚSTICA: Tono Hardware"
            mensaje = "El Gabinete (Cab) de su pedalera debe estar APAGADO."
        else:
            return

        if messagebox.askokcancel(titulo, mensaje):
            ruta = filedialog.askopenfilename(title=f"Seleccionar Tono {tipo}", filetypes=[("Archivos de Audio", "*.wav")])
            if ruta:
                if tipo == "Objetivo":
                    self.ruta_objetivo = ruta
                    self.btn_cargar_obj.config(text="1A. Tono Objetivo Inyectado ✓")
                elif tipo == "Fuente":
                    self.ruta_fuente = ruta
                    self.btn_cargar_fnt.config(text="2. Tono Grabado Inyectado ✓")
                elif tipo == "Objetivo_NAM":
                    self.ruta_objetivo_nam = ruta
                    self.btn_cargar_obj_nam.config(text="1A. Objetivo Inyectado ✓")
                elif tipo == "DI_NAM": 
                    self.ruta_di_nam = ruta
                    self.btn_cargar_di_nam.config(text="2. DI Limpio Inyectado ✓")

    def extraer_ventana_max_energia(self, tensor, fs, segs_max=12):
        """
        Axioma de Optimización: Escanea la matriz y aísla el bloque contiguo 
        de 'segs_max' con la mayor densidad de energía cuadrática media (RMS).
        """
        muestras_limite = segs_max * fs
        if len(tensor) <= muestras_limite:
            return tensor
            
        paso = fs 
        energias = [np.mean(tensor[i:i+paso]**2) for i in range(0, len(tensor)-paso, paso)]
        idx_pico = np.argmax(energias) * paso
        
        inicio = max(0, idx_pico - (muestras_limite // 2))
        fin = inicio + muestras_limite
        return tensor[inicio:fin]                

    def seleccionar_directorio_nam(self):
        ruta_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Cabezales")
        if ruta_dir:
            self.ruta_directorio_nam = ruta_dir
            self.btn_cargar_dir_nam.config(text="3. Carpeta Cabezales ✓")

    def seleccionar_directorio_ir(self):
        ruta_dir = filedialog.askdirectory(title="Seleccionar Carpeta de IRs")
        if ruta_dir:
            self.ruta_directorio_ir = ruta_dir
            self.btn_cargar_dir_ir.config(text="4. Carpeta IRs Inyectada ✓")

    def aislar_hilo_analisis(self):
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan variables en la ecuación.")
            return
        self.btn_analizar.config(text="Calculando LTI...", state=tk.DISABLED)
        threading.Thread(target=self.ejecutar_matematica_dsp).start()

    def ejecutar_matematica_dsp(self):
        try:
            senal_obj, fs_obj = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, fs_fnt = self.motor.cargar_audio(self.ruta_fuente)

            senal_obj = self.extraer_ventana_max_energia(senal_obj, fs_obj)
            senal_fnt = self.extraer_ventana_max_energia(senal_fnt, fs_fnt)
            
            senal_obj_sync, senal_fnt_sync = self.motor.alinear_fase_correlacion(senal_obj, senal_fnt)
            senal_fnt_alineada = self.motor.alinear_energia_rms(senal_obj_sync, senal_fnt_sync)
            
            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj_sync)
            freqs_fnt, psd_fnt = self.motor.calcular_psd_welch(senal_fnt_alineada)
            
            self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_fnt, psd_fnt)
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Analítico", err))
            self.root.after(0, lambda: self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL))

    def renderizar_espectro(self, f_obj, p_obj, f_fnt, p_fnt):
        import matplotlib.pyplot as plt
        
        self.root.geometry("1000x950")
        self.frame_grafica.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.ax.clear()
        
        color_texto = '#E0E0E0'
        color_rejilla = '#333333'
        self.ax.set_facecolor(self.color_fondo)
        
        self.ax.set_title("Dominio de la Frecuencia (Resolución Acústica)", color=color_texto, size=13, weight='bold')
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica", color=color_texto, size=11)
        self.ax.set_ylabel("Densidad Espectral (dB)", color=color_texto, size=11)
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        
        self.ax.grid(True, which="major", color=color_rejilla, linestyle="-", linewidth=0.8, alpha=0.7)
        self.ax.grid(True, which="minor", color=color_rejilla, linestyle=":", linewidth=0.5, alpha=0.3)
        
        p_obj_db = 10 * np.log10(np.maximum(p_obj, 1e-12))
        p_fnt_db = 10 * np.log10(np.maximum(p_fnt, 1e-12))
        
        techo = max(np.max(p_obj_db), np.max(p_fnt_db))
        self.ax.set_ylim([techo - 80, techo + 10]) 

        self.ax.plot(f_obj, p_obj_db, label="Tono Objetivo", color='#00ffcc', alpha=1.0, linewidth=2.5)
        self.ax.plot(f_fnt, p_fnt_db, label="Tono Analizado", color='#ff00ff', alpha=0.9, linewidth=1.5, linestyle='--')
        
        leyenda = self.ax.legend(facecolor=self.color_fondo, edgecolor=color_rejilla, fontsize=10)
        for texto_leyenda in leyenda.get_texts():
            texto_leyenda.set_color(color_texto)
            
        self.figura.tight_layout() 
        self.canvas.draw()
        
        if hasattr(self, 'btn_analizar'):
            self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL)

    def construir_lienzo_espectral(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        self.frame_grafica = ttk.LabelFrame(self.root, text="Matriz de Densidad Espectral de Potencia")
        self.color_fondo = '#1A1A1C'
        
        self.figura = Figure(figsize=(10, 5), dpi=100, facecolor=self.color_fondo)
        self.ax = self.figura.add_subplot(111)
        self.ax.set_facecolor(self.color_fondo) 
        
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.frame_grafica)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def construir_firma_ingenieria(self):
        frame_branding = ttk.Frame(self.root)
        frame_branding.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

        self.btn_limpiar = ttk.Button(frame_branding, text="Limpiar Entorno", width=15, command=self.limpiar_entorno)
        self.btn_limpiar.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_salir = ttk.Button(frame_branding, text="Salir", width=10, command=self.salir_aplicacion)
        self.btn_salir.pack(side=tk.LEFT)

        lbl_texto = ttk.Label(frame_branding, text="Max  |  The Guitar Notebook", style='Branding.TLabel')
        lbl_texto.pack(side=tk.RIGHT, pady=5)

        try:
            img = Image.open(resolver_ruta("logo_tgn.png")).resize((35, 35), Image.Resampling.LANCZOS)
            self.logo_renderizado = ImageTk.PhotoImage(img)
            ttk.Label(frame_branding, image=self.logo_renderizado).pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            pass 

    def limpiar_entorno(self):
        atributos_estado = ['ruta_objetivo', 'ruta_fuente', 'ruta_objetivo_nam', 'ruta_di_nam', 'ruta_directorio_nam', 'ruta_directorio_ir']
        for attr in atributos_estado:
            if hasattr(self, attr):
                delattr(self, attr)
        
        self.btn_cargar_obj_nam.config(text="1A. Objetivo Aislado (.wav)")
        self.btn_cargar_di_nam.config(text="2. Tono DI Limpio (.wav)")
        self.btn_cargar_dir_nam.config(text="3. Carpeta Cabezales (.nam)")
        self.btn_cargar_dir_ir.config(text="4. Carpeta Gabinetes IR (.wav)")

        self.aniquilar_cache_neuronal()
        self.lbl_resultado_nam.config(text="Estado: Esperando tensores...", foreground="") 
        self.btn_cargar_obj.config(text="1A. Inyectar Objetivo Aislado (.wav)")
        self.btn_cargar_fnt.config(text="2. Inyectar Tono Grabado (.wav)")
        
        if hasattr(self, 'frame_grafica'):
            self.frame_grafica.pack_forget()
        if hasattr(self, 'ax'):
            self.ax.clear()
            
        self.root.geometry("1000x750")       
        self.barra_progreso_nam['value'] = 0
        self.lbl_porcentaje_nam.config(text="0%")
        self.barra_progreso_hw['value'] = 0
        self.lbl_porcentaje_hw.config(text="0%")

    def obtener_ruta_licencia(self):
        return os.path.join(os.path.expanduser("~"), ".tgn_licencia.key") 

    def mostrar_ventana_activacion(self):
        ventana_act = tk.Toplevel(self.root)
        ventana_act.title("Activación de Producto")
        ventana_act.geometry("550x300")
        
        try:
            serial_cliente = self.seguridad.extraer_hardware_serial()
        except Exception as e:
            serial_cliente = f"Error: {e}"

        frame_interno = ttk.Frame(ventana_act, padding=20)
        frame_interno.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame_interno, text="Licencia Requerida", font=('SF Pro Display', 16, 'bold')).pack(pady=(0, 10))
        ttk.Label(frame_interno, text="Envíe su Hardware ID a The Guitar Notebook.", justify=tk.CENTER).pack(pady=(0, 15))

        frame_hwid = ttk.Frame(frame_interno)
        frame_hwid.pack(fill=tk.X, pady=5)
        ttk.Label(frame_hwid, text="Hardware ID:", font=('SF Pro Display', 12, 'bold')).pack(side=tk.LEFT)
        
        entrada_hwid = ttk.Entry(frame_hwid, font=('Times New Roman', 13))
        entrada_hwid.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        entrada_hwid.insert(0, serial_cliente)
        entrada_hwid.config(state='readonly') 

        frame_llave = ttk.Frame(frame_interno)
        frame_llave.pack(fill=tk.X, pady=15)
        ttk.Label(frame_llave, text="Llave de Acceso:", font=('SF Pro Display', 12, 'bold')).pack(side=tk.LEFT)
        
        entrada_llave = ttk.Entry(frame_llave, font=('Times New Roman', 13))
        entrada_llave.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        def validar_e_inyectar():
            llave_ingresada = entrada_llave.get().strip()
            if llave_ingresada == self.seguridad.generar_llave_maestra(serial_cliente):
                try:
                    with open(self.obtener_ruta_licencia(), "w") as archivo:
                        archivo.write(llave_ingresada)
                    messagebox.showinfo("Éxito", "Criptografía validada.", parent=ventana_act)
                    ventana_act.destroy()
                except Exception as e:
                    messagebox.showerror("Error de E/S", f"Fallo al escribir:\n{e}", parent=ventana_act)
            else:
                messagebox.showerror("Rechazado", "Llave inválida.", parent=ventana_act)

        ttk.Button(frame_interno, text="Activar Software", command=validar_e_inyectar).pack(pady=10)

    def aniquilar_cache_neuronal(self):
        import shutil
        directorio_temp = os.path.expanduser("~/TGN_Stem_Cache")
        if os.path.exists(directorio_temp):
            try:
                shutil.rmtree(directorio_temp)
            except Exception:
                pass

    def salir_aplicacion(self):
        if messagebox.askokcancel("Cierre", "¿Confirma la finalización de los procesos?"):
            self.aniquilar_cache_neuronal()
            self.root.quit()
            self.root.destroy()

    def mostrar_creditos(self):
        messagebox.showinfo("Acerca del Sistema", "TGN Tone Architect v1.4\nMotor DSP basado en LTI/NAM.\nDesarrollo: Max - The Guitar Notebook")

    def verificar_actualizacion(self):
        messagebox.showinfo("Estado", "El módulo de actualización requiere binarios compilados.")

if __name__ == "__main__":
    import sys
    import multiprocessing
    
    # AXIOMA 1: Soporte estricto para multiprocesamiento en binarios compilados
    multiprocessing.freeze_support() 
    
    # AXIOMA 2: Enrutamiento Neuronal Estricto (Bloqueo de Fork Bomb)
    # Intercepta el subprocess.Popen de motor_dsp.py para ejecutar IA sin abrir la GUI
    if len(sys.argv) >= 3 and sys.argv[1] == "-m" and sys.argv[2] == "demucs.separate":
        from demucs.separate import main as demucs_main
        # Rebanamos la matriz de argumentos (ignoramos el ejecutable y las banderas '-m', 'demucs.separate')
        argumentos_demucs = sys.argv[3:]
        # Ejecutamos la separación tensorial y terminamos el hilo con el código de salida exacto
        sys.exit(demucs_main(argumentos_demucs))
        
    # AXIOMA 3: Inicialización de la Interfaz Gráfica (Flujo Nominal)
    raiz = tk.Tk()
    
    style = ttk.Style()
    if 'aqua' in style.theme_names():
        style.theme_use('aqua') 
    
    style.configure('.', font=('SF Pro Display', 13))
    style.configure('TButton', font=('SF Pro Display', 13))
    style.configure('TLabelframe.Label', font=('SF Pro Display', 14, 'bold'))
    style.configure('Branding.TLabel', font=('SF Pro Display', 11), foreground='#888888')
        
    app = OptimizadorGUI(raiz)
    raiz.mainloop()