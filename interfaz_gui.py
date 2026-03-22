import customtkinter as ctk
import tkinter as tk # Mantenemos tk crudo solo para menús del sistema
import os
import sys
import ctypes
from tkinter import filedialog, messagebox
import threading
from PIL import Image, ImageTk
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

# =========================================================================
# MOTOR MATEMÁTICO C++ (Interfaz de Función Foránea - FFI)
# =========================================================================
class AnalizadorTopologicoUniversal:
    """
    Motor generalizado para la discriminación de sistemas LTV (Espaciales) 
    y NLTI (No Lineales) mediante integración del Factor de Cresta (Cf).
    """
    def __init__(self, ruta_dylib: str):
        if not os.path.exists(ruta_dylib):
            print(f"Advertencia Topológica: Binario Mach-O ausente en {ruta_dylib}. El análisis DSP operará en modo bypass.")
            self.activo = False
            return
            
        self.lib = ctypes.CDLL(ruta_dylib)
        self._configurar_interfaz_binaria()
        
        # Instanciación estricta en la memoria de C++
        self.processor_ptr = self.lib.PluginProcessor_Create()
        self.activo = True

    def _configurar_interfaz_binaria(self):
        self.lib.PluginProcessor_Create.restype = ctypes.c_void_p
        self.lib.PluginProcessor_ProcessBlock.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.c_int]
        self.lib.PluginProcessor_ProcessBlock.restype = None
        self.lib.PluginProcessor_GetState.argtypes = [ctypes.c_void_p]
        self.lib.PluginProcessor_GetState.restype = ctypes.c_int
        self.lib.PluginProcessor_Destroy.argtypes = [ctypes.c_void_p]
        self.lib.PluginProcessor_Destroy.restype = None

    def evaluar_vector_continuo(self, vector_audio: np.ndarray) -> int:
        if not self.activo: return 0
        
        # =================================================================
        # AXIOMA DE DIMENSIONALIDAD: Prevención de Colapso Estéreo
        # =================================================================
        # Si la matriz es multidimensional (ej. Estéreo), la colapsamos a un vector Mono
        # promediando matemáticamente sus canales para evitar falsos positivos de Cresta.
        if vector_audio.ndim > 1:
            # Determinamos cuál eje contiene los canales (típicamente el más pequeño)
            eje_canales = 1 if vector_audio.shape[1] <= 2 else 0
            vector_audio = np.mean(vector_audio, axis=eje_canales)

        # Mapeo estricto a coma flotante simple (IEEE-754)
        if vector_audio.dtype != np.float32:
            if vector_audio.dtype == np.int16:
                vector_audio = vector_audio.astype(np.float32) / 32768.0
            elif vector_audio.dtype == np.int32:
                vector_audio = vector_audio.astype(np.float32) / 2147483648.0
            else:
                vector_audio = vector_audio.astype(np.float32)

        # Imposición del axioma de contigüidad (C-Order) en memoria
        if not vector_audio.flags['C_CONTIGUOUS']:
            vector_audio = np.ascontiguousarray(vector_audio, dtype=np.float32)
            
        longitud = len(vector_audio)
        puntero_buffer = vector_audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        
        # Ejecución asintótica O(N) en el backend C++
        self.lib.PluginProcessor_ProcessBlock(self.processor_ptr, puntero_buffer, longitud)
        return self.lib.PluginProcessor_GetState(self.processor_ptr)

# =========================================================================
# INTERFAZ GRÁFICA PRINCIPAL (MOTOR VECTORIAL: CUSTOMTKINTER)
# =========================================================================
class OptimizadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TGN Tone Architect - The Guitar Notebook")
        self.root.geometry("1050x850") 
        self.fs_origen = 44100
        
        # Configuración del Motor Vectorial
        ctk.set_appearance_mode("dark") 
        ctk.set_default_color_theme("blue") 
        
        self.motor = MotorTonalDSP()
        self.seguridad = CriptografiaHWID()
        
        ruta_motor_cpp = resolver_ruta("TGN_DSP_Engine.dylib")
        self.motor_cpp = AnalizadorTopologicoUniversal(ruta_motor_cpp)

        self.construir_barra_menu()
        
        # Axioma: Construir firma inferior PRIMERO para reservar espacio
        self.construir_firma_ingenieria()
                
        # Chasis Principal
        self.notebook = ctk.CTkTabview(self.root, width=1000, height=750, corner_radius=10)
        self.notebook.pack(fill=ctk.BOTH, expand=True, padx=20, pady=15)

        self.tab_nam = self.notebook.add("Rama A: Búsqueda Correlacional (NAM)")
        self.tab_hardware = self.notebook.add("Rama B: Síntesis Hardware (Filtros FIR)")

        self.frame_grafico = None

        self.construir_rama_nam()
        self.construir_rama_hardware()

    def construir_barra_menu(self):
        """
        Axioma de Integración Nativa (macOS Global Menu Bar).
        Envía los controles al subsistema superior de Apple, 
        fuera del chasis oscuro de la aplicación.
        """
        # Matriz base del menú global
        menubar = tk.Menu(self.root)
        
        # 1. Nodo de Sistema (Créditos y Salida)
        sistema_menu = tk.Menu(menubar, tearoff=0)
        sistema_menu.add_command(label="Acerca de TGN Tone Architect", command=self.mostrar_creditos)
        sistema_menu.add_command(label="Verificar Actualizaciones...", command=self.verificar_actualizacion)
        sistema_menu.add_separator() 
        sistema_menu.add_command(label="Salir del Motor DSP", command=self.salir_aplicacion, accelerator="Cmd+Q")
        
        menubar.add_cascade(label="TGN Sistema", menu=sistema_menu)

        # 2. Nodo de Herramientas Analíticas
        herramientas_menu = tk.Menu(menubar, tearoff=0)
        herramientas_menu.add_command(label="Limpiar Entornos (Reset)", command=self.limpiar_entorno, accelerator="Cmd+L")
        menubar.add_cascade(label="Herramientas", menu=herramientas_menu)

        # Anclaje estricto: Obliga a macOS a proyectar esto en el borde superior del monitor
        self.root.config(menu=menubar)
        
        # Enrutamiento de atajos de teclado (Keybinds) del hardware Mac hacia las funciones
        self.root.bind("<Command-q>", lambda event: self.salir_aplicacion())
        self.root.bind("<Command-l>", lambda event: self.limpiar_entorno())

    def construir_rama_nam(self):
        """Topología Premium: Rama A con Agrupamiento Lógico Simétrico a la Rama B."""
        self.frame_master_nam = ctk.CTkFrame(self.tab_nam, fg_color="transparent")
        self.frame_master_nam.pack(expand=True, fill=ctk.BOTH, padx=10, pady=10)
        
        # --- SECCIÓN SUPERIOR: INYECTORES DE SEÑAL ---
        frame_inputs = ctk.CTkFrame(self.frame_master_nam, fg_color="#212121", corner_radius=12, border_width=1, border_color="#333333")
        frame_inputs.pack(fill=ctk.X, pady=(0, 15), padx=10)

        # Columna Objetivo
        frame_col_obj = ctk.CTkFrame(frame_inputs, fg_color="transparent")
        frame_col_obj.pack(side=tk.LEFT, expand=True, fill=ctk.BOTH, padx=20, pady=20)
        
        ctk.CTkLabel(frame_col_obj, text="DIAGNÓSTICO OBJETIVO", font=('SF Pro Display', 11, 'bold'), text_color="#aaaaaa").pack(anchor=tk.W)
        self.btn_cargar_obj_nam = ctk.CTkButton(frame_col_obj, text="1A. Cargar WAV Aislado", height=35, command=lambda: self.cargar_archivo("Objetivo_NAM"))
        self.btn_cargar_obj_nam.pack(fill=ctk.X, pady=(10, 5))
        
        frame_ia_params = ctk.CTkFrame(frame_col_obj, fg_color="transparent")
        frame_ia_params.pack(fill=ctk.X, pady=5)

        self.var_demucs_hw_nam = ctk.StringVar(value="cpu")
        ctk.CTkOptionMenu(frame_ia_params, variable=self.var_demucs_hw_nam, values=["cpu", "cuda"], width=80, height=25).pack(side=tk.LEFT, padx=(0, 5))

        self.var_demucs_calidad_nam = ctk.StringVar(value="Estándar")
        ctk.CTkOptionMenu(frame_ia_params, variable=self.var_demucs_calidad_nam, values=["Básico", "Estándar", "Pro"], width=110, height=25).pack(side=tk.LEFT)

        self.btn_extraer_ia_nam = ctk.CTkButton(frame_col_obj, text="1B. Extraer con IA", height=35, fg_color="#D04A02", hover_color="#A03A02", command=lambda: self.aislar_hilo_extraccion_ia(rama="NAM"))
        self.btn_extraer_ia_nam.pack(fill=ctk.X, pady=(5, 0))

        # Divisor visual vertical
        ctk.CTkFrame(frame_inputs, width=2, fg_color="#333333").pack(side=tk.LEFT, fill=tk.Y, pady=20)

        # Columna Fuente y Directorios
        frame_col_fnt = ctk.CTkFrame(frame_inputs, fg_color="transparent")
        frame_col_fnt.pack(side=tk.LEFT, expand=True, fill=ctk.BOTH, padx=20, pady=20)
        
        ctk.CTkLabel(frame_col_fnt, text="SEÑAL DE ORIGEN Y BANCOS", font=('SF Pro Display', 11, 'bold'), text_color="#aaaaaa").pack(anchor=tk.W)
        
        self.btn_cargar_di_nam = ctk.CTkButton(frame_col_fnt, text="2. Cargar Tono DI Limpio", height=35, command=lambda: self.cargar_archivo("DI_NAM"))
        self.btn_cargar_di_nam.pack(fill=ctk.X, pady=(10, 5))

        frame_dirs = ctk.CTkFrame(frame_col_fnt, fg_color="transparent")
        frame_dirs.pack(fill=ctk.X, pady=5)

        self.btn_cargar_dir_nam = ctk.CTkButton(frame_dirs, text="3. Banco NAM", height=35, command=self.seleccionar_directorio_nam)
        self.btn_cargar_dir_nam.pack(side=tk.LEFT, expand=True, fill=ctk.X, padx=(0, 5))

        self.btn_cargar_dir_ir = ctk.CTkButton(frame_dirs, text="4. Banco IRs", height=35, command=self.seleccionar_directorio_ir)
        self.btn_cargar_dir_ir.pack(side=tk.LEFT, expand=True, fill=ctk.X)

        # --- SECCIÓN CENTRAL: MOTOR DE BÚSQUEDA ---
        frame_engine = ctk.CTkFrame(self.frame_master_nam, fg_color="#1a1a1a", corner_radius=12, border_width=1, border_color="#1f538d")
        frame_engine.pack(fill=ctk.X, pady=10, padx=10)

        ctk.CTkLabel(frame_engine, text="TOLERANCIA TOPOLÓGICA (MSE LIMIT)", font=('SF Pro Display', 11, 'bold'), text_color="#3b82f6").pack(pady=(15, 5))
        
        valores_tol = ["Perfección Topológica (MSE < 5.0)", "Aceptable Comercial (MSE < 15.0)", "Aproximación (MSE < 30.0)"]
        self.var_tolerancia = ctk.StringVar(value=valores_tol[1])
        self.selector_tolerancia = ctk.CTkOptionMenu(frame_engine, variable=self.var_tolerancia, values=valores_tol, width=500, height=35)
        self.selector_tolerancia.pack(pady=10)

        frame_acciones = ctk.CTkFrame(frame_engine, fg_color="transparent")
        frame_acciones.pack(pady=(10, 20))

        self.btn_buscar_nam = ctk.CTkButton(frame_acciones, text="EJECUTAR MATRIZ COMBINATORIA", width=400, height=45, fg_color="#1f538d", hover_color="#14375e", font=('SF Pro Display', 13, 'bold'), command=self.aislar_hilo_busqueda_nam)
        self.btn_buscar_nam.pack(pady=5)

        # --- SECCIÓN INFERIOR: TELEMETRÍA ---
        self.lbl_resultado_nam = ctk.CTkLabel(self.frame_master_nam, text="SISTEMA LISTO", font=('Monospace', 12), text_color="#00ffcc")
        self.lbl_resultado_nam.pack(pady=5)
        
        self.frame_progreso_nam = ctk.CTkFrame(self.frame_master_nam, fg_color="transparent")
        self.frame_progreso_nam.pack(fill=ctk.X, padx=50, pady=10)
        
        self.barra_progreso_nam = ctk.CTkProgressBar(self.frame_progreso_nam, mode="determinate", height=12, progress_color="#1f538d")
        self.barra_progreso_nam.pack(side=tk.LEFT, fill=ctk.X, expand=True, padx=(0, 15))
        self.barra_progreso_nam.set(0.0) 
        
        self.lbl_porcentaje_nam = ctk.CTkLabel(self.frame_progreso_nam, text="0%", font=('SF Pro Display', 12, 'bold'))
        self.lbl_porcentaje_nam.pack(side=tk.RIGHT, padx=(0, 15))

    def construir_rama_hardware(self):
        self.frame_master_hw = ctk.CTkFrame(self.tab_hardware, fg_color="transparent")
        self.frame_master_hw.pack(expand=True, fill=ctk.BOTH, padx=10, pady=10)
        
        frame_inputs = ctk.CTkFrame(self.frame_master_hw, fg_color="#212121", corner_radius=12, border_width=1, border_color="#333333")
        frame_inputs.pack(fill=ctk.X, pady=(0, 15), padx=10)

        frame_col_obj = ctk.CTkFrame(frame_inputs, fg_color="transparent")
        frame_col_obj.pack(side=tk.LEFT, expand=True, fill=ctk.BOTH, padx=20, pady=20)
        
        ctk.CTkLabel(frame_col_obj, text="DIAGNÓSTICO OBJETIVO", font=('SF Pro Display', 11, 'bold'), text_color="#aaaaaa").pack(anchor=tk.W)
        self.btn_cargar_obj = ctk.CTkButton(frame_col_obj, text="1A. Cargar WAV Aislado", height=35, command=lambda: self.cargar_archivo("Objetivo"))
        self.btn_cargar_obj.pack(fill=ctk.X, pady=(10, 5))
        
        # --- INYECCIÓN DE VARIABLES DE IA (Motor y Calidad) ---
        frame_ia_params = ctk.CTkFrame(frame_col_obj, fg_color="transparent")
        frame_ia_params.pack(fill=ctk.X, pady=5)

        self.var_demucs_hw = ctk.StringVar(value="cpu")
        ctk.CTkOptionMenu(frame_ia_params, variable=self.var_demucs_hw, values=["cpu", "cuda"], width=80, height=25).pack(side=tk.LEFT, padx=(0, 5))

        self.var_demucs_calidad = ctk.StringVar(value="Estándar")
        ctk.CTkOptionMenu(frame_ia_params, variable=self.var_demucs_calidad, values=["Básico", "Estándar", "Pro"], width=110, height=25).pack(side=tk.LEFT)
        # ------------------------------------------------------

        self.btn_extraer_ia = ctk.CTkButton(frame_col_obj, text="1B. Extraer con IA", height=35, fg_color="#D04A02", hover_color="#A03A02", command=lambda: self.aislar_hilo_extraccion_ia(rama="HW"))
        self.btn_extraer_ia.pack(fill=ctk.X, pady=(5, 0))

        ctk.CTkFrame(frame_inputs, width=2, fg_color="#333333").pack(side=tk.LEFT, fill=tk.Y, pady=20)

        frame_col_fnt = ctk.CTkFrame(frame_inputs, fg_color="transparent")
        frame_col_fnt.pack(side=tk.LEFT, expand=True, fill=ctk.BOTH, padx=20, pady=20)
        
        ctk.CTkLabel(frame_col_fnt, text="SEÑAL DE ORIGEN (DI/CAB)", font=('SF Pro Display', 11, 'bold'), text_color="#aaaaaa").pack(anchor=tk.W)
        self.btn_cargar_fnt = ctk.CTkButton(frame_col_fnt, text="2. Cargar Tono Grabado", height=35, command=lambda: self.cargar_archivo("Fuente"))
        self.btn_cargar_fnt.pack(fill=ctk.X, pady=(10, 0))

        frame_engine = ctk.CTkFrame(self.frame_master_hw, fg_color="#1a1a1a", corner_radius=12, border_width=1, border_color="#1f538d")
        frame_engine.pack(fill=ctk.X, pady=10, padx=10)

        ctk.CTkLabel(frame_engine, text="CONFIGURACIÓN DEL PROCESADOR (DSP TARGET)", font=('SF Pro Display', 11, 'bold'), text_color="#3b82f6").pack(pady=(15, 5))
        
        valores_hw = [
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
        ]
        self.variable_hardware = ctk.StringVar(value=valores_hw[0])
        self.selector_hardware = ctk.CTkOptionMenu(frame_engine, variable=self.variable_hardware, values=valores_hw, width=500, height=35, dynamic_resizing=False)
        self.selector_hardware.pack(pady=10)

        frame_acciones = ctk.CTkFrame(frame_engine, fg_color="transparent")
        frame_acciones.pack(pady=(10, 20))

        self.btn_analizar = ctk.CTkButton(frame_acciones, text="ANALIZAR ESPECTRO", width=200, height=45, font=('SF Pro Display', 13, 'bold'), command=self.aislar_hilo_analisis)
        self.btn_analizar.pack(side=tk.LEFT, padx=10)

        self.btn_exportar = ctk.CTkButton(frame_acciones, text="SINTETIZAR FILTRO", width=200, height=45, fg_color="#28a745", hover_color="#218838", font=('SF Pro Display', 13, 'bold'), command=self.aislar_hilo_sintesis)
        self.btn_exportar.pack(side=tk.LEFT, padx=10)

        self.frame_progreso_hw = ctk.CTkFrame(self.frame_master_hw, fg_color="transparent")
        self.frame_progreso_hw.pack(fill=ctk.X, padx=50, pady=10)
        
        self.barra_progreso_hw = ctk.CTkProgressBar(self.frame_progreso_hw, mode="determinate", height=12, progress_color="#1f538d")
        self.barra_progreso_hw.pack(side=tk.LEFT, fill=ctk.X, expand=True, padx=(0, 15))
        self.barra_progreso_hw.set(0.0)
        
        self.lbl_porcentaje_hw = ctk.CTkLabel(self.frame_progreso_hw, text="0%", font=('SF Pro Display', 12, 'bold'))
        self.lbl_porcentaje_hw.pack(side=tk.RIGHT, padx=(0, 15))

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
                self.btn_extraer_ia_nam.configure(text="Separando Matriz... (Espere)", state="disabled")
                hw_val = self.var_demucs_hw_nam.get()
                calidad_val = self.var_demucs_calidad_nam.get()
                self.barra_progreso_nam.set(0.0)
                self.lbl_porcentaje_nam.configure(text="0%")
            else:
                self.btn_extraer_ia.configure(text="Separando Matriz... (Espere)", state="disabled")
                hw_val = self.var_demucs_hw.get()
                calidad_val = self.var_demucs_calidad.get()
                self.barra_progreso_hw.set(0.0)
                self.lbl_porcentaje_hw.configure(text="0%")
            
            mapa_calidad = {"Básico": QualityLevel.DRAFT, "Estándar": QualityLevel.STANDARD, "Pro": QualityLevel.PRO}
            hw_seleccionado = ComputeDevice.CUDA if hw_val == "cuda" else ComputeDevice.CPU
            calidad_seleccionada = mapa_calidad.get(calidad_val, QualityLevel.STANDARD)

            config_demucs = DemucsInferenceConfig(device=hw_seleccionado, quality=calidad_seleccionada, stem=TargetStem.GUITAR)
            self.runner_ia = DemucsRunner(config=config_demucs, input_path=ruta_mezcla, output_dir=directorio_temp)
            
            self.runner_ia.start_extraction(
                on_progress=lambda p: self.root.after(0, self.actualizar_progreso_ia, p, rama),
                on_complete=lambda code: self.root.after(0, self.finalizar_extraccion_ia, code, directorio_temp, ruta_mezcla, rama),
                on_error=lambda err: self.root.after(0, self.error_extraccion_ia, err, rama)
            )

    def actualizar_progreso_ia(self, valor, rama):
        valor_flotante = valor / 100.0
        if rama == "NAM":
            self.barra_progreso_nam.set(valor_flotante)
            self.lbl_porcentaje_nam.configure(text=f"{int(valor)}%")
        else:
            self.barra_progreso_hw.set(valor_flotante)
            self.lbl_porcentaje_hw.configure(text=f"{int(valor)}%")

    def finalizar_extraccion_ia(self, return_code: int, directorio_temp: str, ruta_mezcla: str, rama: str):
        if return_code != 0:
            self.error_extraccion_ia(f"El hilo secundario abortó con estado: {return_code}", rama)
            return
            
        nombre_base = os.path.splitext(os.path.basename(ruta_mezcla))[0]
        ruta_tensor = os.path.join(directorio_temp, "htdemucs_6s", nombre_base, "guitar.wav")
        
        if os.path.exists(ruta_tensor):
            if rama == "NAM":
                self.ruta_objetivo_nam = ruta_tensor
                self.btn_cargar_obj_nam.configure(text="1A. Objetivo Inyectado (Vía IA) ✓")
                self.btn_extraer_ia_nam.configure(text="1B. Extraer de Mezcla (IA)", state="normal")
                self.actualizar_progreso_ia(100.0, "NAM")
            else:
                self.ruta_objetivo = ruta_tensor
                self.btn_cargar_obj.configure(text="1A. Objetivo Inyectado (Vía IA) ✓")
                self.btn_extraer_ia.configure(text="1B. Extraer de Mezcla Completa (IA)", state="normal")
                self.actualizar_progreso_ia(100.0, "HW")
            
            messagebox.showinfo("Inferencia Exitosa", f"Matriz aislada rigurosamente e inyectada como LTI objetivo.\n\nVector de destino:\n{ruta_tensor}")
        else:
            self.error_extraccion_ia(f"Fallo de E/S estocástico. El tensor no se materializó en:\n{ruta_tensor}", rama)

    def error_extraccion_ia(self, error_msg: str, rama: str):
        if rama == "NAM":
            self.btn_extraer_ia_nam.configure(text="1B. Extraer de Mezcla (IA)", state="normal")
        else:
            self.btn_extraer_ia.configure(text="1B. Extraer de Mezcla Completa (IA)", state="normal")
        messagebox.showerror("Colapso Neuronal", f"Fallo en el motor de separación:\n{error_msg}")

    def aislar_hilo_sintesis(self):
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan las matrices de audio.")
            return

        try:
            # 1. EVALUACIÓN DSP EN EL HILO PRINCIPAL (Seguro para la GUI)
            senal_obj, fs_obj = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, fs_fnt = self.motor.cargar_audio(self.ruta_fuente)
            umbral_muestras_ir = fs_obj * 0.5 

            diagnostico_global = ""
            alerta_ltv_global = False

            # =================================================================
            # EVALUACIÓN LTV (Reverberación/Espacialidad Vía C++)
            # AXIOMA: Detección NLTI extirpada por solapamiento estocástico.
            # =================================================================
            if len(senal_obj) > umbral_muestras_ir:
                estado_obj = self.motor_cpp.evaluar_vector_continuo(senal_obj)
                if estado_obj == 1:
                    diagnostico_global += "▶ Tono Objetivo: [LTV] Anomalía Espacial Confirmada (Reverb/Delay).\n"
                    alerta_ltv_global = True

            if len(senal_fnt) > umbral_muestras_ir:
                estado_fnt = self.motor_cpp.evaluar_vector_continuo(senal_fnt)
                if estado_fnt == 1:
                    diagnostico_global += "▶ Tono Fuente: [LTV] Anomalía Espacial Confirmada (Reverb/Delay).\n"
                    alerta_ltv_global = True

            # Invocación SEGURA del menú en el hilo principal SOLO si hay Reverb
            if diagnostico_global:
                decision = self.invocar_menu_resolucion_compleja(diagnostico_global, alerta_ltv_global)
                if decision == "Cancelar":
                    return
            
            directorio_escritorio = os.path.expanduser("~/Desktop")
            ruta_guardado = filedialog.asksaveasfilename(
                initialdir=directorio_escritorio,
                defaultextension=".wav", 
                filetypes=[("WAV", "*.wav")]
            )
            
            if not ruta_guardado:
                return
                                       
            self.btn_exportar.configure(text="Sintetizando...", state="disabled")
            threading.Thread(target=self.ejecutar_sintesis_dsp, args=(ruta_guardado, self.variable_hardware.get(), senal_obj, senal_fnt, fs_obj, fs_fnt)).start()

        except Exception as e:
            messagebox.showerror("Colapso Topológico", str(e))

    def desplegar_metricas_hardware(self, muestras, sr_salida, formato_bits, low_cut_hpf, high_cut_lpf, ruta_guardado, alerta_brickwall):
        hpf_formateado = round(float(low_cut_hpf), 2)
        lpf_formateado = round(float(high_cut_lpf), 2)
        
        advertencia_ia = ""
        if alerta_brickwall:
            advertencia_ia = (
                "\n\n[ADVERTENCIA DE INTEGRIDAD ESPECTRAL]\n"
                "El algoritmo ha detectado una caída espectral de tipo 'Brickwall'. "
                "Esta pendiente es físicamente anómala para hardware analógico e indica que el archivo "
                "fue amputado digitalmente (probablemente por separación neuronal como Demucs). "
                "El valor del High Cut refleja exactamente el límite donde la IA destruyó la información armónica.\n\n"
                "▶ ACCIÓN MANUAL: Incremente el High Cut en su hardware si desea extrapolar el brillo original."
            )

        texto_resultado = (
            f"Matriz FIR compilada con deconvolución anecoica.\n\n"
            f"Hardware: {muestras} muestras | {sr_salida} Hz | {formato_bits}\n\n"
            f"PARÁMETROS DE HARDWARE SUGERIDOS:\n"
            f"▶ Low Cut (HPF): {hpf_formateado} Hz\n"
            f"▶ High Cut (LPF): {lpf_formateado} Hz\n"
            f"{advertencia_ia}\n\n"
            f"Destino:\n{ruta_guardado}"
        )
        
        messagebox.showinfo("Síntesis Exitosa", texto_resultado, parent=self.root)

    def ejecutar_sintesis_dsp(self, ruta_guardado, seleccion_hw, senal_obj, senal_fnt, fs_obj, fs_fnt):
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

            senal_obj = self.extraer_ventana_max_energia(senal_obj, fs_obj)
            senal_fnt = self.extraer_ventana_max_energia(senal_fnt, fs_fnt)
            
            senal_obj_sync, senal_fnt_sync = self.motor.alinear_fase_correlacion(senal_obj, senal_fnt)
            senal_fnt_alineada = self.motor.alinear_energia_rms(senal_obj_sync, senal_fnt_sync)

            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj_sync)
            _, psd_fnt = self.motor.calcular_psd_welch(senal_fnt_alineada)

            low_cut_hpf, high_cut_lpf, alerta_brickwall = self.motor.calcular_fronteras_espectrales(freqs_obj, psd_obj)
            
            vector_ir = self.motor.sintetizar_filtro_fir(freqs_obj, psd_obj, psd_fnt, muestras_salida=muestras)
            vector_ir = self.motor.deconvolucion_ceps_anecoica(vector_ir)

            if fs_obj != sr_salida:
                vector_ir = librosa.resample(vector_ir, orig_sr=fs_obj, target_sr=sr_salida)
                vector_ir = vector_ir[:muestras] 

            sf.write(ruta_guardado, vector_ir, sr_salida, subtype=formato_bits)

            self.root.after(0, self.desplegar_metricas_hardware, muestras, sr_salida, formato_bits, low_cut_hpf, high_cut_lpf, ruta_guardado, alerta_brickwall)
        
        except Exception as e:
            self.root.after(0, self.desplegar_error_hardware, str(e))
        finally:
            self.root.after(0, lambda: self.btn_exportar.configure(text="SINTETIZAR FILTRO", state="normal"))

    def desplegar_error_hardware(self, mensaje_error):
        messagebox.showerror("Colapso en Síntesis", mensaje_error, parent=self.root)

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
            self.root.after(0, lambda: self.btn_buscar_nam.configure(text="Ejecutar Matriz Combinatoria", state="normal"))
            return

        try:
            senal_obj, fs_obj = self.motor.cargar_audio(ruta_obj_local)
            senal_di, fs_di = self.motor.cargar_audio(ruta_di_local)

            senal_obj = self.extraer_ventana_max_energia(senal_obj, fs_obj)
            senal_di = self.extraer_ventana_max_energia(senal_di, fs_di)

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

            _, _, alerta_brickwall = self.motor.calcular_fronteras_espectrales(freqs_obj_welch, psd_obj_welch)

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
                    texto_final = f"Cabezal (.nam): {amp_ganador}\nIR: {ir_ganador}"
                    color_texto = "#00ffcc" 
                    
                    if alerta_brickwall:
                        texto_final += "\n\n[ADVERTENCIA ESPECTRAL]: El Tono Objetivo fue amputado por IA.\nEl algoritmo emparejó el tono oscuro resultante."
                        color_texto = "#ffaa00" 
                        
                    self.root.after(0, lambda t=texto_final, c=color_texto: self.lbl_resultado_nam.configure(text=t, text_color=c))
                    self.root.after(0, self.renderizar_espectro_premium, freqs_ganador, psd_obj_ganador, freqs_ganador, psd_ganador, self.frame_master_nam)
                else:
                    texto_fallo = f"Rechazado. MSE: {menor_mse:.2f}\nSupera el umbral topológico."
                    self.root.after(0, lambda t=texto_fallo: self.lbl_resultado_nam.configure(text=t, text_color="red"))
            else:
                self.root.after(0, lambda: self.lbl_resultado_nam.configure(text="Fallo analítico: Matriz evaluada en vacío.", text_color="red"))
                
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Analítico", err))
        finally:
            self.root.after(0, lambda: self.btn_buscar_nam.configure(text="Ejecutar Matriz Combinatoria", state="normal"))

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
        
        self.btn_buscar_nam.configure(text="Escaneando... (Espere)", state="disabled")
        self.lbl_resultado_nam.configure(text="Calculando ...")
        self.barra_progreso_nam.set(0.0)
        self.lbl_porcentaje_nam.configure(text="0%")
        
        threading.Thread(target=self.ejecutar_busqueda_dsp).start()

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
                    self.btn_cargar_obj.configure(text="1A. Tono Objetivo Inyectado ✓")
                elif tipo == "Fuente":
                    self.ruta_fuente = ruta
                    self.btn_cargar_fnt.configure(text="2. Tono Grabado Inyectado ✓")
                elif tipo == "Objetivo_NAM":
                    self.ruta_objetivo_nam = ruta
                    self.btn_cargar_obj_nam.configure(text="1A. Objetivo Inyectado ✓")
                elif tipo == "DI_NAM": 
                    self.ruta_di_nam = ruta
                    self.btn_cargar_di_nam.configure(text="2. DI Limpio Inyectado ✓")

    def extraer_ventana_max_energia(self, tensor, fs, segs_max=12):
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
            self.btn_cargar_dir_nam.configure(text="3. Carpeta Cabezales ✓")

    def seleccionar_directorio_ir(self):
        ruta_dir = filedialog.askdirectory(title="Seleccionar Carpeta de IRs")
        if ruta_dir:
            self.ruta_directorio_ir = ruta_dir
            self.btn_cargar_dir_ir.configure(text="4. Carpeta IRs Inyectada ✓")

    def aislar_hilo_analisis(self):
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan variables en la ecuación.")
            return
        self.btn_analizar.configure(text="Calculando LTI...", state="disabled")
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
            
            self.root.after(0, self.renderizar_espectro_premium, freqs_obj, psd_obj, freqs_fnt, psd_fnt, self.frame_master_hw)
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Analítico", err))
            self.root.after(0, lambda: self.btn_analizar.configure(text="ANALIZAR ESPECTRO", state="normal"))

    def renderizar_espectro_premium(self, f_obj, p_obj, f_test, p_test, marco_destino): 
        """Renderiza la comparación espectral dinámicamente según la rama activa."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.pyplot as plt

        # AXIOMA DE EXPANSIÓN GEOMÉTRICA: Agrandamos la ventana para acomodar un gráfico masivo
        self.root.geometry("1100x1000")

        if self.frame_grafico:
            self.frame_grafico.destroy()

        # Inyectamos el gráfico en el marco_destino correspondiente (Rama A o Rama B) con altura extendida (height=350)
        self.frame_grafico = ctk.CTkFrame(marco_destino, fg_color="#111111", height=350, corner_radius=12)
        self.frame_grafico.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
        fig.patch.set_facecolor('#111111') 
        ax.set_facecolor('#111111')       

        ax.plot(f_obj, 10 * np.log10(p_obj + 1e-12), color='#ff5555', label='Tono Objetivo', linewidth=1.5, alpha=0.8)
        ax.plot(f_test, 10 * np.log10(p_test + 1e-12), color='#00ffcc', label='Tono Evaluado', linewidth=1.2, alpha=0.9)

        ax.grid(True, which='both', color='#333333', linestyle='--', linewidth=0.5)
        ax.set_xscale('log') 
        ax.set_xlim(40, 20000)
        ax.set_ylim(-80, 5)
        
        for spine in ax.spines.values():
            spine.set_color('#444444')

        ax.tick_params(colors='#888888', labelsize=8)
        
        # AXIOMA TOPOLÓGICO: Inyección de la Leyenda de Trazos
        ax.legend(facecolor='#111111', edgecolor='#333333', labelcolor='#E0E0E0', fontsize=10, loc='lower left')
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        plt.close(fig) 
        
        if hasattr(self, 'btn_analizar'):
            self.btn_analizar.configure(text="ANALIZAR ESPECTRO", state="normal")

    def construir_firma_ingenieria(self):
        frame_branding = ctk.CTkFrame(self.root, fg_color="transparent")
        frame_branding.pack(side=tk.BOTTOM, fill=ctk.X, padx=20, pady=10)

        self.btn_limpiar = ctk.CTkButton(frame_branding, text="Limpiar Entorno", width=140, fg_color="#444444", hover_color="#666666", command=self.limpiar_entorno)
        self.btn_limpiar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_salir = ctk.CTkButton(frame_branding, text="Salir", width=100, fg_color="#8b0000", hover_color="#5c0000", command=self.salir_aplicacion)
        self.btn_salir.pack(side=tk.LEFT)

        lbl_texto = ctk.CTkLabel(frame_branding, text="Max  |  The Guitar Notebook", font=('SF Pro Display', 12), text_color='#888888')
        lbl_texto.pack(side=tk.RIGHT, pady=5)

        try:
            img = Image.open(resolver_ruta("logo_tgn.png")).resize((35, 35), Image.Resampling.LANCZOS)
            self.logo_renderizado = ctk.CTkImage(light_image=img, dark_image=img, size=(35, 35))
            ctk.CTkLabel(frame_branding, image=self.logo_renderizado, text="").pack(side=tk.RIGHT, padx=10)
        except Exception:
            pass

    def limpiar_entorno(self):
        atributos_estado = ['ruta_objetivo', 'ruta_fuente', 'ruta_objetivo_nam', 'ruta_di_nam', 'ruta_directorio_nam', 'ruta_directorio_ir']
        for attr in atributos_estado:
            if hasattr(self, attr):
                delattr(self, attr)
        
        self.btn_cargar_obj_nam.configure(text="1A. Objetivo Aislado (.wav)")
        self.btn_cargar_di_nam.configure(text="2. Tono DI Limpio (.wav)")
        self.btn_cargar_dir_nam.configure(text="3. Carpeta Cabezales (.nam)")
        self.btn_cargar_dir_ir.configure(text="4. Carpeta Gabinetes IR (.wav)")

        self.aniquilar_cache_neuronal()
        self.lbl_resultado_nam.configure(text="Estado: Esperando tensores...", text_color="#aaaaaa") 
        self.btn_cargar_obj.configure(text="1A. Cargar WAV Aislado")
        self.btn_cargar_fnt.configure(text="2. Cargar Tono Grabado")
        
        if hasattr(self, 'frame_grafico') and self.frame_grafico:
            self.frame_grafico.pack_forget()
            self.frame_grafico.destroy()
            self.frame_grafico = None
            
        self.barra_progreso_nam.set(0.0)
        self.lbl_porcentaje_nam.configure(text="0%")
        self.barra_progreso_hw.set(0.0)
        self.lbl_porcentaje_hw.configure(text="0%")

    def obtener_ruta_licencia(self):
        return os.path.join(os.path.expanduser("~"), ".tgn_licencia.key") 

    def mostrar_ventana_activacion(self):
        ventana_act = ctk.CTkToplevel(self.root)
        ventana_act.title("Activación de Producto")
        ventana_act.geometry("550x300")
        ventana_act.attributes("-topmost", True)
        ventana_act.grab_set()
        
        try:
            serial_cliente = self.seguridad.extraer_hardware_serial()
        except Exception as e:
            serial_cliente = f"Error: {e}"

        ctk.CTkLabel(ventana_act, text="Licencia Requerida", font=('SF Pro Display', 18, 'bold')).pack(pady=(20, 10))
        ctk.CTkLabel(ventana_act, text="Envíe su Hardware ID a The Guitar Notebook para recibir su clave.", text_color="#aaaaaa").pack(pady=(0, 20))

        frame_hwid = ctk.CTkFrame(ventana_act, fg_color="transparent")
        frame_hwid.pack(fill=ctk.X, padx=30, pady=5)
        ctk.CTkLabel(frame_hwid, text="Hardware ID:", font=('SF Pro Display', 12, 'bold')).pack(side=tk.LEFT)
        
        entrada_hwid = ctk.CTkEntry(frame_hwid, font=('Monospace', 13), width=350)
        entrada_hwid.pack(side=tk.RIGHT)
        entrada_hwid.insert(0, serial_cliente)
        entrada_hwid.configure(state='readonly') 

        frame_llave = ctk.CTkFrame(ventana_act, fg_color="transparent")
        frame_llave.pack(fill=ctk.X, padx=30, pady=15)
        ctk.CTkLabel(frame_llave, text="Llave de Acceso:", font=('SF Pro Display', 12, 'bold')).pack(side=tk.LEFT)
        
        entrada_llave = ctk.CTkEntry(frame_llave, font=('Monospace', 13), width=350)
        entrada_llave.pack(side=tk.RIGHT)

        def validar_e_inyectar():
            llave_ingresada = entrada_llave.get().strip()
            if llave_ingresada == self.seguridad.generar_llave_maestra(serial_cliente):
                try:
                    with open(self.obtener_ruta_licencia(), "w") as archivo:
                        archivo.write(llave_ingresada)
                    messagebox.showinfo("Éxito", "Criptografía validada. El sistema está ahora operativo.", parent=ventana_act)
                    ventana_act.destroy()
                except Exception as e:
                    messagebox.showerror("Error de E/S", f"Fallo al escribir:\n{e}", parent=ventana_act)
            else:
                messagebox.showerror("Rechazado", "Llave inválida. Contáctese con el proveedor.", parent=ventana_act)

        ctk.CTkButton(ventana_act, text="Activar Software", fg_color="#28a745", hover_color="#218838", command=validar_e_inyectar).pack(pady=20)

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

    def invocar_menu_resolucion_compleja(self, diagnostico, tiene_anomalias_tiempo):
        ventana_decision = ctk.CTkToplevel(self.root)
        ventana_decision.title("Intervención Analítica")
        ventana_decision.geometry("700x320")
        ventana_decision.attributes("-topmost", True)
        ventana_decision.grab_set()
        
        ctk.CTkLabel(ventana_decision, text="Anomalía Topológica Detectada en los Tensores", 
                     font=('SF Pro Display', 15, 'bold'), text_color="#D04A02").pack(pady=(20, 5))
                     
        ctk.CTkLabel(ventana_decision, text=diagnostico, wraplength=650, justify="left", 
                     font=('SF Pro Display', 13), text_color="#E0E0E0").pack(pady=10, padx=20)
        
        opcion_var = ctk.StringVar()
        opciones = ["Continuar con Matriz Híbrida (El motor DSP compensará las anomalías automáticamente)"]
        
        if tiene_anomalias_tiempo:
            opciones.insert(0, "Aislamiento Estricto - Priorizar ataque y suprimir colas espaciales")
            
        opciones.append("Cancelar Síntesis")
        opcion_var.set(opciones[0])
        
        menu = ctk.CTkOptionMenu(ventana_decision, variable=opcion_var, values=opciones, width=600, height=35)
        menu.pack(pady=15)
        
        decision_final = "Cancelar"
        def confirmar():
            nonlocal decision_final
            decision_final = opcion_var.get().split(" - ")[0]
            ventana_decision.destroy()
            
        btn_confirmar = ctk.CTkButton(ventana_decision, text="Validar y Ejecutar", height=40, font=('SF Pro Display', 13, 'bold'), 
                                      fg_color="#D04A02", hover_color="#A03A02", command=confirmar)
        btn_confirmar.pack(pady=15)
        
        self.root.wait_window(ventana_decision)
        return decision_final    

# =========================================================================
# RUTINA DE EJECUCIÓN DEL SISTEMA
# =========================================================================
if __name__ == "__main__":
    import multiprocessing
    
    multiprocessing.freeze_support() 
    
    if len(sys.argv) >= 3 and sys.argv[1] == "-m" and sys.argv[2] == "demucs.separate":
        from demucs.separate import main as demucs_main
        argumentos_demucs = sys.argv[3:]
        sys.exit(demucs_main(argumentos_demucs))
        
    raiz = ctk.CTk() 
    app = OptimizadorGUI(raiz)
    raiz.mainloop()