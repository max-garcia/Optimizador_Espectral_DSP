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
        self.root.geometry("1000x650") 
        
        self.motor = MotorTonalDSP()
        self.seguridad = CriptografiaHWID()

        self.construir_barra_menu()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.tab_nam = ttk.Frame(self.notebook)
        self.tab_hardware = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_nam, text="Rama A: Búsqueda Correlacional (NAM)")
        self.notebook.add(self.tab_hardware, text="Rama B: Síntesis Hardware (Filtros FIR)")

        self.modo_escaneo = tk.StringVar(value="IR")
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

        self.btn_cargar_obj_nam = ttk.Button(frame_controles_nam, text="1. Tono Objetivo (.wav)", width=30, command=lambda: self.cargar_archivo("Objetivo_NAM"))
        self.btn_cargar_obj_nam.grid(row=0, column=0, padx=15, pady=5)

        self.btn_cargar_di_nam = ttk.Button(frame_controles_nam, text="2. Tono DI Limpio (.wav)", width=30, command=lambda: self.cargar_archivo("DI_NAM"))
        self.btn_cargar_di_nam.grid(row=0, column=1, padx=15, pady=5)

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

        self.frame_progreso = ttk.Frame(frame_controles_nam)
        self.frame_progreso.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        self.barra_progreso = ttk.Progressbar(self.frame_progreso, orient="horizontal", mode="determinate")
        self.barra_progreso.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 5))
        
        self.lbl_porcentaje = ttk.Label(self.frame_progreso, text="0%", font=('Times New Roman', 12, 'bold'))
        self.lbl_porcentaje.pack(side=tk.RIGHT, padx=(0, 15))

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
        
        # Selectores Paramétricos para IA
        frame_ia_params = ttk.Frame(frame_obj)
        frame_ia_params.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_ia_params, text="Motor:", font=('SF Pro Display', 10)).grid(row=0, column=0, sticky=tk.W)
        self.var_demucs_hw = tk.StringVar(value="cpu")
        ttk.Combobox(frame_ia_params, textvariable=self.var_demucs_hw, values=("cpu", "cuda"), state="readonly", width=8).grid(row=0, column=1, padx=5)

        ttk.Label(frame_ia_params, text="Calidad:", font=('SF Pro Display', 10)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.var_demucs_calidad = tk.StringVar(value="Estándar")
        ttk.Combobox(frame_ia_params, textvariable=self.var_demucs_calidad, values=("Básico", "Estándar", "Pro"), state="readonly", width=8).grid(row=1, column=1, padx=5)

        self.btn_extraer_ia = ttk.Button(frame_obj, text="1B. Extraer de Mezcla Completa (IA)", width=35, command=self.aislar_hilo_extraccion_ia)
        self.btn_extraer_ia.pack()

        self.btn_cargar_fnt = ttk.Button(frame_controles, text="2. Inyectar Tono Grabado (.wav)", width=30, command=lambda: self.cargar_archivo("Fuente"))
        self.btn_cargar_fnt.grid(row=0, column=1, padx=15, pady=10)

        lbl_ecosistema = ttk.Label(frame_controles, text="3. Ecosistema de Exportación:")
        lbl_ecosistema.grid(row=1, column=0, columnspan=2, pady=(15, 5))
        
        self.variable_hardware = tk.StringVar()
        self.selector_hardware = ttk.Combobox(frame_controles, textvariable=self.variable_hardware, state="readonly", width=45, justify='center')
        self.selector_hardware['values'] = (
            "Line 6 Helix / Pod Go (1024 muestras | 48 kHz)",
            "Neural DSP Quad Cortex (1024 muestras | 48 kHz)",
            "Fractal Audio Axe-Fx / FM (2048 muestras | 48 kHz)",
            "Headrush FX Prime / Core (2048 muestras | 48 kHz)",
            "Fender Tone Master Pro (2048 muestras | 48 kHz)",
            "Kemper Profiler (2048 muestras | 44.1 kHz)",
            "IK Multimedia ToneX (1024 muestras | 44.1 kHz)"
        )
        self.selector_hardware.current(0)
        self.selector_hardware.grid(row=2, column=0, columnspan=2, pady=5)

        frame_botones_hw = ttk.Frame(frame_controles)
        frame_botones_hw.grid(row=3, column=0, columnspan=2, pady=25)

        self.btn_analizar = ttk.Button(frame_botones_hw, text="Calcular Ecuación Espectral", width=25, command=self.aislar_hilo_analisis)
        self.btn_analizar.pack(side=tk.LEFT, padx=10)

        self.btn_exportar = ttk.Button(frame_botones_hw, text="Sintetizar Filtro FIR", width=25, command=self.aislar_hilo_sintesis)
        self.btn_exportar.pack(side=tk.LEFT, padx=10)

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

    def mostrar_creditos(self):
        texto = (
            "TGN Tone Architect v1.3\n\n"
            "Motor de análisis acústico y Tone Match basado en LTI/NAM.\n"
            "Desarrollado para la evaluación determinista de hardware.\n\n"
            "Diseño de Sonido y Código: Max - The Guitar Notebook"
        )
        messagebox.showinfo("Acerca del Sistema", texto)

    def verificar_actualizacion(self):
        version_local = "v1.3" 
        url_api = "https://api.github.com/repos/max-garcia/Optimizador_Espectral_DSP/releases/latest"
        
        try:
            respuesta = requests.get(url_api, timeout=5)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                version_remota = datos.get("tag_name", "Desconocida")
                
                if version_remota != version_local and version_remota != "Desconocida":
                    activos = datos.get("assets", [])
                    url_descarga_dmg = None
                    for activo in activos:
                        if activo.get("name", "").endswith(".dmg"):
                            url_descarga_dmg = activo.get("browser_download_url")
                            break
                            
                    if not url_descarga_dmg:
                        messagebox.showerror("Error de Paquete", "La nueva versión existe, pero no se encontró un archivo .dmg compilado en el servidor.")
                        return

                    mensaje = (
                        f"Actualización Crítica Disponible: {version_remota}\n\n"
                        f"El sistema descargará el paquete acústico y sobrescribirá "
                        f"la arquitectura actual.\n\n"
                        f"¿Desea iniciar la inyección de código ahora?"
                    )
                    
                    if messagebox.askyesno("Sincronización de Sistema", mensaje):
                        self.ejecutar_auto_updater(url_descarga_dmg, version_remota)
                else:
                    messagebox.showinfo("Estado", "El software está en su última versión matemática.")
            else:
                messagebox.showerror("Error HTTP", f"El servidor rechazó la conexión. Código: {respuesta.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Colapso de Red", f"Fallo al contactar el servidor:\n{e}")

    def ejecutar_auto_updater(self, url_dmg, nueva_version):
        ventana_act = tk.Toplevel(self.root)
        ventana_act.title("Actualizando TGN Tone Architect")
        ventana_act.geometry("450x150")
        ventana_act.resizable(False, False)
        
        lbl_info = ttk.Label(ventana_act, text=f"Descargando versión {nueva_version}...", font=('SF Pro Display', 12, 'bold'))
        lbl_info.pack(pady=(20, 10))
        
        barra_progreso = ttk.Progressbar(ventana_act, orient="horizontal", mode="determinate", length=350)
        barra_progreso.pack(pady=5)
        
        lbl_porcentaje = ttk.Label(ventana_act, text="0%", font=('Times New Roman', 12))
        lbl_porcentaje.pack()

        ventana_act.update()

        def repote_descarga(bloque_num, tamano_bloque, tamano_total):
            descargado = bloque_num * tamano_bloque
            if tamano_total > 0:
                porcentaje = min(100, int((descargado / tamano_total) * 100))
                barra_progreso['value'] = porcentaje
                lbl_porcentaje.config(text=f"{porcentaje}%")
                ventana_act.update_idletasks()

        ruta_dmg_temp = "/tmp/TGN_Update.dmg"
        ruta_script_sh = "/tmp/tgn_updater.sh"
        
        if getattr(sys, 'frozen', False):
            ruta_app_actual = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "../../.."))
        else:
            ruta_app_actual = os.path.abspath(os.path.dirname(__file__))

        def hilo_descarga_y_ejecucion():
            try:
                urllib.request.urlretrieve(url_dmg, ruta_dmg_temp, repote_descarga)
                lbl_info.config(text="Desacoplando y sobrescribiendo binarios...")
                ventana_act.update()
                
                if getattr(sys, 'frozen', False):
                    script_bash = f"""#!/bin/bash
                    sleep 2
                    hdiutil attach "{ruta_dmg_temp}" -mountpoint /Volumes/TGN_Update -nobrowse
                    rm -rf "{ruta_app_actual}"
                    cp -R /Volumes/TGN_Update/*.app "{ruta_app_actual}"
                    hdiutil detach /Volumes/TGN_Update -force
                    rm "{ruta_dmg_temp}"
                    rm "{ruta_script_sh}"
                    open "{ruta_app_actual}"
                    """
                    
                    with open(ruta_script_sh, "w") as f:
                        f.write(script_bash)
                    os.chmod(ruta_script_sh, 0o755)
                    
                    subprocess.Popen(['/bin/bash', ruta_script_sh], start_new_session=True)
                    os._exit(0)
                else:
                    messagebox.showinfo("Entorno de Desarrollo", "Descarga completada en /tmp/. La sobrescritura automática solo opera sobre el binario compilado (.app).", parent=ventana_act)
                    ventana_act.destroy()

            except Exception as e:
                messagebox.showerror("Colapso Topológico", f"Fallo en la síntesis de actualización:\n{e}", parent=ventana_act)
                ventana_act.destroy()

        threading.Thread(target=hilo_descarga_y_ejecucion).start()
      
    def obtener_ruta_licencia(self):
        """
        Axioma de E/S: Resuelve un vector de almacenamiento seguro en el espacio del usuario.
        Almacena la llave como un archivo oculto para evitar violaciones de permisos en /Applications.
        """
        import os
        directorio_usuario = os.path.expanduser("~")
        return os.path.join(directorio_usuario, ".tgn_licencia.key") 

    def salir_aplicacion(self):
        if messagebox.askokcancel("Cierre", "¿Confirma la finalización de los procesos?"):
            self.aniquilar_cache_neuronal()
            self.root.quit()
            self.root.destroy()    

    def cargar_archivo(self, tipo):
        if tipo == "Objetivo_NAM" or tipo == "Objetivo":
            titulo = "Axioma Topológico: Tono Objetivo"
            mensaje = (
                "Para que el trabajo sea preciso, el archivo debe cumplir estas condiciones:\n\n"
                "• Formato: .wav (16 o 24 bits).\n"
                "• Contenido: El Stem (pista aislada) de la guitarra del disco o referencia.\n"
                "• Condición Crítica: Procure extraer el audio de una sección con mínima interferencia "
                "(sin colisión severa con platillos o voz) para reducir la pérdida de fase y artefactos."
            )
        elif tipo == "DI_NAM":
            titulo = "ADVERTENCIA ACÚSTICA: Tono DI Limpio"
            mensaje = (
                "El Tono DI debe ser la señal eléctrica virgen para evitar el colapso de la red neuronal.\n\n"
                "• Formato: .wav (16 o 24 bits).\n"
                "• Condición Crítica: Grabado directamente de la entrada Hi-Z (Instrumento) de su interfaz.\n\n"
                "PROHIBICIONES ESTRICTAS:\n"
                "✕ Ningún amplificador físico o virtual (Plugin).\n"
                "✕ Ningún gabinete (IR) o simulación de altavoz.\n"
                "✕ Ningún pedal, compresión o ecualización en el DAW."
            )
        elif tipo == "Fuente":
            titulo = "ADVERTENCIA ACÚSTICA: Tono Hardware (Grabado)"
            mensaje = (
                "Para aislar la respuesta lineal del filtro FIR, la señal debe contener "
                "únicamente la distorsión del preamplificador.\n\n"
                "• Formato: .wav (16 o 24 bits).\n"
                "• Condición Crítica: El bloque de Gabinete (Cab) o IR en su pedalera debe estar ESTRICTAMENTE APAGADO.\n"
                "• Ajuste Previo: Iguale auditivamente la cantidad de ganancia/distorsión de su equipo "
                "con la distorsión del Tono Objetivo antes de grabar."
            )
        else:
            return

        confirmacion = messagebox.askokcancel(titulo, mensaje)
        
        if confirmacion:
            ruta = filedialog.askopenfilename(title=f"Seleccionar Tono {tipo}", filetypes=[("Archivos de Audio", "*.wav")])
            if ruta:
                if tipo == "Objetivo":
                    self.ruta_objetivo = ruta
                    self.btn_cargar_obj.config(text="1. Tono Objetivo Inyectado ✓")
                elif tipo == "Fuente":
                    self.ruta_fuente = ruta
                    self.btn_cargar_fnt.config(text="2. Tono Grabado Inyectado ✓")
                elif tipo == "Objetivo_NAM":
                    self.ruta_objetivo_nam = ruta
                    self.btn_cargar_obj_nam.config(text="1. Objetivo Inyectado ✓")
                elif tipo == "DI_NAM": 
                    self.ruta_di_nam = ruta
                    self.btn_cargar_di_nam.config(text="2. DI Limpio Inyectado ✓")

    def aislar_hilo_extraccion_ia(self):
        ruta_mezcla = filedialog.askopenfilename(title="Seleccionar Mezcla Comercial", filetypes=[("Archivos de Audio", "*.wav *.mp3 *.flac")])
        if not ruta_mezcla:
            return
            
        advertencia = (
            "La separación neuronal exige rigor computacional.\n\n"
            "El subproceso operará fuera del hilo principal para mantener la GUI fluida.\n"
            "¿Desea inicializar la inferencia IA?"
        )
        
        if messagebox.askokcancel("Carga Computacional", advertencia):
            import os
            from motor_dsp import DemucsRunner, DemucsInferenceConfig, ComputeDevice, TargetStem, QualityLevel
            
            directorio_temp = os.path.expanduser("~/TGN_Stem_Cache")
            os.makedirs(directorio_temp, exist_ok=True)
            
            self.btn_extraer_ia.config(text="Separando Matriz... (Espere)", state=tk.DISABLED)
            
            mapa_calidad = {
                "Básico": QualityLevel.DRAFT,
                "Estándar": QualityLevel.STANDARD,
                "Pro": QualityLevel.PRO
            }
            hw_seleccionado = ComputeDevice.CUDA if self.var_demucs_hw.get() == "cuda" else ComputeDevice.CPU
            calidad_seleccionada = mapa_calidad.get(self.var_demucs_calidad.get(), QualityLevel.STANDARD)

            config_demucs = DemucsInferenceConfig(
                device=hw_seleccionado,
                quality=calidad_seleccionada,
                stem=TargetStem.GUITAR
            )

            self.runner_ia = DemucsRunner(config=config_demucs, input_path=ruta_mezcla, output_dir=directorio_temp)
            
            self.barra_progreso['value'] = 0
            self.lbl_porcentaje.config(text="0%")

            # Ejecución con inyección de dependencias estocásticas
            self.runner_ia.start_extraction(
                on_progress=lambda p: self.root.after(0, self.actualizar_progreso, p),
                on_complete=lambda code: self.root.after(0, self.finalizar_extraccion_ia, code, directorio_temp, ruta_mezcla),
                on_error=lambda err: self.root.after(0, self.error_extraccion_ia, err)
            )
    def ejecutar_extraccion_ia(self, ruta_mezcla, directorio_temp):
        try:
            ruta_tensor_aislado = self.motor.aislar_tensor_guitarra(ruta_mezcla, directorio_temp)
            
            # Inyectamos el resultado estocástico directamente como nuestro tono objetivo LTI
            self.ruta_objetivo = ruta_tensor_aislado
            
            self.root.after(0, lambda: self.btn_cargar_obj.config(text="1A. Objetivo Inyectado (Vía IA) ✓"))
            self.root.after(0, lambda: messagebox.showinfo("Inferencia Exitosa", f"Tensor de guitarra aislado y asignado a la ecuación LTI.\n\nRuta: {ruta_tensor_aislado}"))
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Neuronal", err))
        finally:
            self.root.after(0, lambda: self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state=tk.NORMAL))


    def seleccionar_directorio_nam(self):
        ruta_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Búsqueda")
        if ruta_dir:
            self.ruta_directorio_nam = ruta_dir
            self.btn_cargar_dir_nam.config(text="3. Carpeta Cabezales ✓")

    def seleccionar_directorio_ir(self):
        ruta_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Gabinetes IR")
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
            # 1. Extracción en memoria
            senal_obj, fs = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)
            
            # 2. Sincronización de Fase Exacta
            senal_obj_sync, senal_fnt_sync = self.motor.alinear_fase_correlacion(senal_obj, senal_fnt)
            
            # 3. Alineación de Energía RMS
            senal_fnt_alineada = self.motor.alinear_energia_rms(senal_obj_sync, senal_fnt_sync)
            
            # 4. Cálculo de Densidad Espectral (Welch lineal)
            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj_sync)
            freqs_fnt, psd_fnt = self.motor.calcular_psd_welch(senal_fnt_alineada)
            
            # 5. Inyección del render al hilo principal
            self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_fnt, psd_fnt)
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Analítico", err))
            self.root.after(0, lambda: self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL))

    def renderizar_espectro(self, f_obj, p_obj, f_fnt, p_fnt):
        import numpy as np
        import matplotlib.pyplot as plt
        
        self.root.geometry("1000x950")
        self.frame_grafica.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.ax.clear()
        
        color_texto = '#E0E0E0'
        color_rejilla = '#333333'
        self.ax.set_facecolor(self.color_fondo)
        
        plt.rcParams['font.family'] = 'SF Pro Display'
        fuente_titulo = {'color': color_texto, 'size': 13, 'weight': 'bold'}
        fuente_ejes = {'color': color_texto, 'size': 11}
        
        self.ax.set_title("Dominio de la Frecuencia (Resolución Acústica)", fontdict=fuente_titulo, pad=15)
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica", fontdict=fuente_ejes)
        self.ax.set_ylabel("Densidad Espectral (dB)", fontdict=fuente_ejes)
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        
        self.ax.grid(True, which="major", color=color_rejilla, linestyle="-", linewidth=0.8, alpha=0.7)
        self.ax.grid(True, which="minor", color=color_rejilla, linestyle=":", linewidth=0.5, alpha=0.3)
        
        for spine in self.ax.spines.values():
            spine.set_color(color_rejilla)
            spine.set_linewidth(1)
            
        for label in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            label.set_fontname('Times New Roman')
            label.set_color(color_texto)
            label.set_fontsize(10)
        
        p_obj = np.nan_to_num(p_obj, nan=1e-12, posinf=1e-12, neginf=1e-12)
        p_fnt = np.nan_to_num(p_fnt, nan=1e-12, posinf=1e-12, neginf=1e-12)
        
        p_obj_db = 10 * np.log10(np.maximum(p_obj, 1e-12))
        p_fnt_db = 10 * np.log10(np.maximum(p_fnt, 1e-12))
        
        techo = max(np.max(p_obj_db), np.max(p_fnt_db))
        self.ax.set_ylim([techo - 80, techo + 10]) 

        self.ax.plot(f_obj, p_obj_db, label="Tono Objetivo (Disco)", 
                     color='#00ffcc', alpha=1.0, linewidth=2.5)
        
        self.ax.plot(f_fnt, p_fnt_db, label="Tono Analizado (Hardware)", 
                     color='#ff00ff', alpha=0.9, linewidth=1.5, linestyle='--')
        
        leyenda = self.ax.legend(facecolor=self.color_fondo, edgecolor=color_rejilla, fontsize=10)
        
        if leyenda: 
            for texto_leyenda in leyenda.get_texts():
                texto_leyenda.set_color(color_texto)
                texto_leyenda.set_fontname('SF Pro Display')
            
        self.figura.tight_layout() 
        self.canvas.draw()
        
        if hasattr(self, 'btn_analizar'):
            self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL)

    def aislar_hilo_sintesis(self):
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan las matrices de audio.")
            return
        
        try:
            serial_fisico = self.seguridad.extraer_hardware_serial()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_fisico)
            
            # NUEVO: Invocación de la ruta segura
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

        # NUEVO: Forzar al sistema a ofrecer el Escritorio del usuario como destino de escritura
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
    
    def ejecutar_sintesis_dsp(self, ruta_guardado, seleccion_hw):
        try:
            muestras = 1024
            sr_salida = 48000
            
            if "Fractal" in seleccion_hw or "Headrush" in seleccion_hw or "Tone Master" in seleccion_hw:
                muestras = 2048
                sr_salida = 48000
            elif "Kemper" in seleccion_hw:
                muestras = 2048
                sr_salida = 44100
            elif "ToneX" in seleccion_hw:
                muestras = 1024
                sr_salida = 44100

            # 1. Cargar tensores acústicos
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)
            
            # 2. Sincronización de Fase (Correlación Cruzada)
            senal_obj_sync, senal_fnt_sync = self.motor.alinear_fase_correlacion(senal_obj, senal_fnt)
            
            # 3. Alineación de Energía
            senal_fnt_alineada = self.motor.alinear_energia_rms(senal_obj_sync, senal_fnt_sync)

            # 4. Extracción Espectral
            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj_sync)
            _, psd_fnt = self.motor.calcular_psd_welch(senal_fnt_alineada)

            # 5. Síntesis LTI (Requiere frecuencias para el suavizado)
            vector_ir = self.motor.sintetizar_filtro_fir(freqs_obj, psd_obj, psd_fnt, muestras_salida=muestras)
            
            # 6. Remuestreo y Exportación
            self.motor.exportar_ir(vector_ir, ruta_guardado, target_sr_export=sr_salida)

            self.root.after(0, lambda: messagebox.showinfo(
                "Síntesis Exitosa", 
                f"Matriz FIR compilada para el ecosistema seleccionado.\n\n"
                f"Longitud: {muestras} muestras\n"
                f"Frecuencia Reloj: {sr_salida} Hz\n"
                f"Destino: {ruta_guardado}"
            ))
        
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso en Síntesis", err))
        finally:
            self.root.after(0, lambda: self.btn_exportar.config(text="Sintetizar Filtro FIR", state=tk.NORMAL))

    def actualizar_progreso(self, valor):
        self.barra_progreso['value'] = valor
        self.lbl_porcentaje.config(text=f"{int(valor)}%")

    def aislar_hilo_busqueda_nam(self):
        if not hasattr(self, 'ruta_objetivo_nam') or not hasattr(self, 'ruta_directorio_nam'):
            messagebox.showerror("Error Topológico", "Faltan variables en la ecuación. Inyecte los tensores requeridos.")
            return

        try:
            import os
            serial_fisico = self.seguridad.extraer_hardware_serial()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_fisico)
            
            # NUEVO: Invocación de la ruta segura
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
        
        self.barra_progreso['value'] = 0
        self.lbl_porcentaje.config(text="0%")
        
        threading.Thread(target=self.ejecutar_busqueda_dsp).start()

    def ejecutar_busqueda_dsp(self):
        import numpy as np
        import os
        import threading
        import gc  # <--- Inyección del colector de basura

        try:
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo_nam)
            senal_di, _ = self.motor.cargar_audio(self.ruta_di_nam)

            archivos_nam = [f for f in os.listdir(self.ruta_directorio_nam) if f.endswith('.nam')]
            
            banco_irs = {}
            if hasattr(self, 'ruta_directorio_ir'):
                for arch_ir in [f for f in os.listdir(self.ruta_directorio_ir) if f.endswith('.wav')]:
                    banco_irs[arch_ir] = self.motor.cargar_ir_referencia(os.path.join(self.ruta_directorio_ir, arch_ir))
            else:
                banco_irs["Bypass_Directo"] = np.array([1.0])

            menor_mse = float('inf')
            amp_ganador = None
            ir_ganador = None
            psd_ganador = None
            freqs_ganador = None
            
            total_iteraciones = len(archivos_nam) * len(banco_irs)
            iteracion_actual = 0

            for nombre_nam in archivos_nam:
                try:
                    senal_amp = self.motor.inferencia_neuronal_nam(os.path.join(self.ruta_directorio_nam, nombre_nam), senal_di)

                    if senal_amp is None or np.max(np.abs(senal_amp)) < 1e-6 or np.isnan(senal_amp).any():
                        print(f"Axioma fallido: El tensor {nombre_nam} generó silencio absoluto.")
                        iteracion_actual += len(banco_irs)
                        continue

                    for nombre_ir, vector_ir in banco_irs.items():
                        senal_final = senal_amp if nombre_ir == "Bypass_Directo" else self.motor.aplicar_gabinete_referencia(senal_amp, vector_ir)
                        
                        # Inyección estricta de alineación por fase
                        senal_obj_sync, senal_final_sync = self.motor.alinear_fase_correlacion(senal_obj, senal_final)
                        senal_final_alineada = self.motor.alinear_energia_rms(senal_obj_sync, senal_final_sync)
                        
                        freqs_obj_sync, psd_obj_sync = self.motor.calcular_psd_welch(senal_obj_sync)
                        _, psd_test = self.motor.calcular_psd_welch(senal_final_alineada)
                        
                        if np.isnan(psd_test).any() or np.max(psd_test) < 1e-12:
                            iteracion_actual += 1
                            continue
                            
                        mse_actual = self.motor.calcular_mse_espectral(psd_obj_sync, psd_test)

                        if mse_actual < menor_mse:
                            menor_mse = mse_actual
                            amp_ganador = nombre_nam
                            ir_ganador = nombre_ir
                            psd_ganador = np.copy(psd_test)
                            freqs_ganador = np.copy(freqs_obj_sync)

                        iteracion_actual += 1
                        progreso = (iteracion_actual / total_iteraciones) * 100
                        self.root.after(0, lambda p=progreso: self.actualizar_progreso(p))
                        
                except Exception as e:
                    print(f"Error estructural procesando {nombre_nam}: {e}")
                    iteracion_actual += len(banco_irs)
                finally:
                    # AXIOMA DE VOLATILIDAD (Previene Out of Memory en matrices grandes)
                    if 'senal_amp' in locals():
                        del senal_amp
                    gc.collect()

            if amp_ganador and psd_ganador is not None:
                nivel = self.var_tolerancia.get()
                umbral = 5.0 if "Perfección" in nivel else 15.0 if "Aceptable" in nivel else 30.0
                
                if menor_mse <= umbral:
                    texto_final = f"Amplificador (.nam): {amp_ganador}\nIR: {ir_ganador}"
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_final, foreground="#00ffcc"))
                    
                    _, psd_obj_render = self.motor.calcular_psd_welch(senal_obj[:len(freqs_ganador)*2]) 
                    self.root.after(0, self.renderizar_espectro, freqs_ganador, psd_obj_render, freqs_ganador, psd_ganador)
                else:
                    texto_fallo = f"Rechazado. MSE: {menor_mse:.2f}\nSupera el umbral topológico."
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_fallo, foreground="red"))
            else:
                self.root.after(0, lambda: self.lbl_resultado_nam.config(text="Fallo: La matriz devolvió tensores vacíos.", foreground="red"))
                
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Colapso Analítico", err))
        finally:
            self.root.after(0, lambda: self.btn_buscar_nam.config(text="Ejecutar Matriz Combinatoria", state=tk.NORMAL))
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
            ruta_logo = resolver_ruta("logo_tgn.png")
            img = Image.open(ruta_logo)
            img = img.resize((35, 35), Image.Resampling.LANCZOS)
            self.logo_renderizado = ImageTk.PhotoImage(img)

            lbl_logo = ttk.Label(frame_branding, image=self.logo_renderizado)
            lbl_logo.pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            print(f"Fallo gráfico: {e}") 

    def limpiar_entorno(self):
        atributos_estado = [
            'ruta_objetivo', 'ruta_fuente', 
            'ruta_objetivo_nam', 'ruta_di_nam', 
            'ruta_directorio_nam', 'ruta_directorio_ir'
        ]
        for attr in atributos_estado:
            if hasattr(self, attr):
                delattr(self, attr)
        
        self.btn_cargar_obj_nam.config(text="1. Tono Objetivo (.wav)")
        self.btn_cargar_di_nam.config(text="2. Tono DI Limpio (.wav)")
        self.btn_cargar_dir_nam.config(text="3. Carpeta Cabezales (.nam)")
        self.btn_cargar_dir_ir.config(text="4. Carpeta Gabinetes IR (.wav)")

        self.aniquilar_cache_neuronal()
        
        self.lbl_resultado_nam.config(text="Estado: Esperando tensores...", foreground="") 
        
        self.btn_cargar_obj.config(text="1. Inyectar Tono Objetivo (.wav)")
        self.btn_cargar_fnt.config(text="2. Inyectar Tono Grabado (.wav)")
        
        if hasattr(self, 'frame_grafica'):
            self.frame_grafica.pack_forget()
        if hasattr(self, 'ax'):
            self.ax.clear()
            
        self.root.geometry("1000x650")       
        
        self.barra_progreso['value'] = 0
        self.lbl_porcentaje.config(text="0%")

    def mostrar_ventana_activacion(self):
        ventana_act = tk.Toplevel(self.root)
        ventana_act.title("Activación de Producto - The Guitar Notebook")
        ventana_act.geometry("550x300")
        ventana_act.resizable(False, False)
        
        try:
            serial_cliente = self.seguridad.extraer_hardware_serial()
        except Exception as e:
            serial_cliente = f"Error de lectura: {e}"

        frame_interno = ttk.Frame(ventana_act, padding=20)
        frame_interno.pack(fill=tk.BOTH, expand=True)

        lbl_titulo = ttk.Label(frame_interno, text="Licencia Requerida", font=('SF Pro Display', 16, 'bold'))
        lbl_titulo.pack(pady=(0, 10))

        lbl_instruccion = ttk.Label(frame_interno, 
                                    text="Para habilitar la síntesis de filtros FIR, envíe su Hardware ID\n"
                                         "a The Guitar Notebook para adquirir su llave criptográfica.",
                                    justify=tk.CENTER, font=('SF Pro Display', 13))
        lbl_instruccion.pack(pady=(0, 15))

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
            import os
            llave_ingresada = entrada_llave.get().strip()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_cliente)
            
            if llave_ingresada == hash_esperado:
                # NUEVO: Guarda la licencia en la ruta del usuario
                ruta_licencia = self.obtener_ruta_licencia()
                try:
                    with open(ruta_licencia, "w") as archivo:
                        archivo.write(llave_ingresada)
                    messagebox.showinfo("Éxito", "Criptografía validada. El Optimizador Espectral está operativo.", parent=ventana_act)
                    ventana_act.destroy()
                except Exception as e:
                    messagebox.showerror("Error de E/S", f"No se pudo escribir el archivo en el sistema:\n{e}", parent=ventana_act)
            else:
                messagebox.showerror("Rechazado", "La llave criptográfica no corresponde a este Hardware ID.", parent=ventana_act)

        btn_activar = ttk.Button(frame_interno, text="Activar Software", command=validar_e_inyectar)
        btn_activar.pack(pady=10)

    def ejecutar_busqueda_dsp(self):
        import numpy as np
        import os
        import threading
        import gc  # <--- Inyección del colector de basura

        # 1. AISLAMIENTO ESTRUCTURAL (Prevención de Condición de Carrera)
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
            # 2. CARGA DE TENSORES
            senal_obj, _ = self.motor.cargar_audio(ruta_obj_local)
            senal_di, _ = self.motor.cargar_audio(ruta_di_local)

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

            # 3. OPTIMIZACIÓN ASINTÓTICA: Cálculo de Welch Objetivo fuera del bucle de O(n)
            # Extraemos la matriz LTI base una sola vez, ahorrando ciclos de CPU.
            freqs_obj_welch, psd_obj_welch = self.motor.calcular_psd_welch(senal_obj)
            rms_obj = np.sqrt(np.mean(senal_obj**2))

            for nombre_nam in archivos_nam:
                try:
                    senal_amp = self.motor.inferencia_neuronal_nam(os.path.join(ruta_dir_nam_local, nombre_nam), senal_di)

                    if senal_amp is None or np.max(np.abs(senal_amp)) < 1e-6 or np.isnan(senal_amp).any():
                        print(f"Axioma fallido: El tensor {nombre_nam} generó silencio absoluto.")
                        iteracion_actual += len(banco_irs)
                        continue

                    for nombre_ir, vector_ir in banco_irs.items():
                        senal_final = senal_amp if nombre_ir == "Bypass_Directo" else self.motor.aplicar_gabinete_referencia(senal_amp, vector_ir)
                        
                        # 4. AXIOMA DE INVARIANZA ESPECTRAL: Sin recortes de fase.
                        # Alineamos puramente la energía RMS soportando archivos de distinta longitud.
                        rms_fnt = np.sqrt(np.mean(senal_final**2))
                        if rms_fnt > 1e-12:
                            senal_final_alineada = senal_final * (rms_obj / rms_fnt)
                        else:
                            senal_final_alineada = senal_final
                            
                        # Extracción Welch directa sobre la matriz asimétrica
                        _, psd_test = self.motor.calcular_psd_welch(senal_final_alineada)
                        
                        if np.isnan(psd_test).any() or np.max(psd_test) < 1e-12:
                            iteracion_actual += 1
                            continue
                            
                        mse_actual = self.motor.calcular_mse_espectral(psd_obj_welch, psd_test)

                        # Actualización de escalares y conservación de tensores LTI óptimos
                        if mse_actual < menor_mse:
                            menor_mse = mse_actual
                            amp_ganador = nombre_nam
                            ir_ganador = nombre_ir
                            psd_ganador = np.copy(psd_test)
                            freqs_ganador = np.copy(freqs_obj_welch)
                            psd_obj_ganador = np.copy(psd_obj_welch) # Capturamos el renderizado perfecto

                        iteracion_actual += 1
                        progreso = (iteracion_actual / total_iteraciones) * 100
                        self.root.after(0, lambda p=progreso: self.actualizar_progreso(p))
                        
                except Exception as e:
                    print(f"Error estructural procesando {nombre_nam}: {e}")
                    iteracion_actual += len(banco_irs)
                finally:
                    # 5. AXIOMA DE VOLATILIDAD (Gestión Estricta de RAM)
                    if 'senal_amp' in locals():
                        del senal_amp
                    gc.collect()

            # 6. RESOLUCIÓN GRÁFICA Y DE ESTADO
            if amp_ganador and psd_ganador is not None and psd_obj_ganador is not None:
                nivel = self.var_tolerancia.get()
                umbral = 5.0 if "Perfección" in nivel else 15.0 if "Aceptable" in nivel else 30.0
                
                if menor_mse <= umbral:
                    texto_final = f"Amplificador (.nam): {amp_ganador}\nIR: {ir_ganador}"
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_final, foreground="#00ffcc"))
                    
                    # Inyección del render usando el tensor exacto sin truncar dimensiones temporales
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
    # =========================================================================
    # AXIOMAS NEURONALES UNIFICADOS (Purgando duplicados)
    # =========================================================================
    def aislar_hilo_extraccion_ia(self):
        ruta_mezcla = filedialog.askopenfilename(title="Seleccionar Mezcla Comercial", filetypes=[("Archivos de Audio", "*.wav *.mp3 *.flac")])
        if not ruta_mezcla:
            return
            
        advertencia = (
            "La separación neuronal exige rigor computacional.\n\n"
            "El subproceso operará fuera del hilo principal para mantener la GUI fluida.\n"
            "¿Desea inicializar la inferencia IA?"
        )
        
        if messagebox.askokcancel("Carga Computacional", advertencia):
            import os
            from motor_dsp import DemucsRunner, DemucsInferenceConfig, ComputeDevice, TargetStem, QualityLevel
            
            directorio_temp = os.path.expanduser("~/TGN_Stem_Cache")
            os.makedirs(directorio_temp, exist_ok=True)
            
            self.btn_extraer_ia.config(text="Separando Matriz... (Espere)", state=tk.DISABLED)
            
            mapa_calidad = {
                "Básico": QualityLevel.DRAFT,
                "Estándar": QualityLevel.STANDARD,
                "Pro": QualityLevel.PRO
            }
            hw_seleccionado = ComputeDevice.CUDA if self.var_demucs_hw.get() == "cuda" else ComputeDevice.CPU
            calidad_seleccionada = mapa_calidad.get(self.var_demucs_calidad.get(), QualityLevel.STANDARD)

            config_demucs = DemucsInferenceConfig(
                device=hw_seleccionado,
                quality=calidad_seleccionada,
                stem=TargetStem.GUITAR
            )

            self.runner_ia = DemucsRunner(config=config_demucs, input_path=ruta_mezcla, output_dir=directorio_temp)
            
            self.barra_progreso['value'] = 0
            self.lbl_porcentaje.config(text="0%")

            self.runner_ia.start_extraction(
                on_progress=lambda p: self.root.after(0, self.actualizar_progreso, p),
                on_complete=lambda code: self.root.after(0, self.finalizar_extraccion_ia, code, directorio_temp, ruta_mezcla),
                on_error=lambda err: self.root.after(0, self.error_extraccion_ia, err)
            )

    def finalizar_extraccion_ia(self, return_code: int, directorio_temp: str, ruta_mezcla: str):
        import os
        
        if return_code != 0:
            self.error_extraccion_ia(f"El hilo secundario abortó con estado: {return_code}")
            return
            
        nombre_base = os.path.splitext(os.path.basename(ruta_mezcla))[0]
        ruta_tensor = os.path.join(directorio_temp, "htdemucs_6s", nombre_base, "guitar.wav")
        
        if os.path.exists(ruta_tensor):
            self.ruta_objetivo = ruta_tensor
            self.btn_cargar_obj.config(text="1A. Objetivo Inyectado (Vía IA) ✓")
            self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state="normal")
            self.actualizar_progreso(100.0)
            
            messagebox.showinfo(
                "Inferencia Exitosa", 
                f"Matriz aislada rigurosamente e inyectada como LTI objetivo.\n\nVector de destino:\n{ruta_tensor}"
            )
        else:
            self.error_extraccion_ia(f"Fallo de E/S estocástico. El tensor no se materializó en:\n{ruta_tensor}")

    def error_extraccion_ia(self, error_msg: str):
        self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state=tk.NORMAL)
        messagebox.showerror("Colapso Neuronal", f"Fallo en el motor de separación:\n{error_msg}")
    def error_extraccion_ia(self, error_msg: str):
        """ Callback de manejo de fallos en T_GUI """
        self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state=tk.NORMAL)
        messagebox.showerror("Colapso Neuronal", f"Fallo en el motor de separación:\n{error_msg}")

    def finalizar_extraccion_ia(self, return_code: int, directorio_temp: str, ruta_mezcla: str):
        import os
        
        if return_code != 0:
            self.error_extraccion_ia(f"El hilo secundario abortó con estado: {return_code}")
            return
            
        # 1. Resolución del identificador original (sin extensión geométrica)
        # Si ruta_mezcla es "/Usuarios/Max/Master_Cancion.wav", nombre_base será "Master_Cancion"
        nombre_base = os.path.splitext(os.path.basename(ruta_mezcla))[0]
        
        # 2. Ensamblaje topológico del árbol de directorios de Demucs
        ruta_tensor = os.path.join(directorio_temp, "htdemucs_6s", nombre_base, "guitar.wav")
        
        # 3. Validación Binaria (Axioma de Existencia)
        if os.path.exists(ruta_tensor):
            # Mutación de memoria autorizada
            self.ruta_objetivo = ruta_tensor
            
            # Reversión de los controles de la interfaz al estado nominal
            self.btn_cargar_obj.config(text="1A. Objetivo Inyectado (Vía IA) ✓")
            self.btn_extraer_ia.config(text="1B. Extraer de Mezcla Completa (IA)", state="normal")
            self.actualizar_progreso(100.0)
            
            from tkinter import messagebox
            messagebox.showinfo(
                "Inferencia Exitosa", 
                f"Matriz aislada rigurosamente e inyectada como LTI objetivo.\n\nVector de destino:\n{ruta_tensor}"
            )
        else:
            self.error_extraccion_ia(f"Fallo de E/S estocástico. El tensor no se materializó en:\n{ruta_tensor}")


    def aniquilar_cache_neuronal(self):
        """
        Axioma de Volatilidad: Libera estrictamente el espacio de almacenamiento temporal
        ocupado por los tensores estocásticos de Demucs.
        """
        import os
        import shutil
        
        directorio_temp = os.path.expanduser("~/TGN_Stem_Cache")
        
        # Verificación del estado de existencia en el sistema de archivos
        if os.path.exists(directorio_temp):
            try:
                # Eliminación recursiva del árbol de directorios
                shutil.rmtree(directorio_temp)
                print(f"Memoria de almacenamiento liberada: {directorio_temp}")
            except Exception as e:
                # Captura silenciosa: El sistema operativo podría tener el archivo bloqueado (File Lock).
                # No lanzamos un messagebox para no interrumpir el cierre del programa.
                print(f"Colapso en la aniquilación de caché: {e}")
if __name__ == "__main__":
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
