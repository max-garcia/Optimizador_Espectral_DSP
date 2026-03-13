import tkinter as tk
import os
import sys
from tkinter import filedialog, messagebox
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import requests
from PIL import Image, ImageTk

# Importación estricta del núcleo matemático
from motor_dsp import MotorTonalDSP
from gestor_licencias import CriptografiaHWID  

def resolver_ruta(ruta_relativa):
    """Calcula el vector absoluto al recurso gráfico, resolviendo el entorno _MEIPASS de PyInstaller."""
    try:
        ruta_base = sys._MEIPASS
    except Exception:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, ruta_relativa)

class OptimizadorGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("TGN Tone Architect - The Guitar Notebook")
        self.root.geometry("1000x420")
        
        # Instancia del núcleo matemático y criptográfico
        self.motor = MotorTonalDSP()
        self.seguridad = CriptografiaHWID()

        # 1. INYECCIÓN DEL MENÚ LOCAL (Anclaje Superior Absoluto)
        self.construir_barra_menu()

        # 2. TOPOLOGÍA BIMODAL (Pestañas con expansión de fluidos)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.tab_nam = ttk.Frame(self.notebook)
        self.tab_hardware = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_nam, text="Rama A: Búsqueda Correlacional (NAM)")
        self.notebook.add(self.tab_hardware, text="Rama B: Síntesis Hardware (Filtros FIR)")

        # Variable de estado
        self.modo_escaneo = tk.StringVar(value="IR")

        # 3. CONSTRUCCIÓN DE RAMAS Y LIENZO
        self.construir_rama_nam()
        self.construir_rama_hardware()
        self.construir_lienzo_espectral()

        # 4. INYECCIÓN DE LA FIRMA (Anclaje Inferior Absoluto)
        self.construir_firma_ingenieria()   

    def construir_barra_menu(self):
        """Construye una barra de menú local forzada dentro de la ventana principal."""
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
        """Renderiza la Rama A con anclaje de fluidos y barra de progreso escalar."""
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

        # Matriz de Progreso (Vector Horizontal)
        self.frame_progreso = ttk.Frame(frame_controles_nam)
        self.frame_progreso.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        self.barra_progreso = ttk.Progressbar(self.frame_progreso, orient="horizontal", mode="determinate")
        self.barra_progreso.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 5))
        
        # Tipografía matemática estricta para el vector numérico
        self.lbl_porcentaje = ttk.Label(self.frame_progreso, text="0%", font=('Times New Roman', 12, 'bold'))
        self.lbl_porcentaje.pack(side=tk.RIGHT, padx=(0, 15))

        self.lbl_resultado_nam = ttk.Label(frame_controles_nam, text="Estado: Esperando tensores...", font=('SF Pro Display', 12, 'bold'), justify='center')
        self.lbl_resultado_nam.grid(row=5, column=0, columnspan=2, pady=5)

    def construir_rama_hardware(self):
        """Renderiza la Rama B con anclaje dinámico."""
        self.frame_master_hw = ttk.Frame(self.tab_hardware)
        self.frame_master_hw.pack(expand=True, fill=tk.BOTH)

        frame_controles = ttk.Frame(self.frame_master_hw)
        frame_controles.pack(expand=True, pady=10)

        self.btn_cargar_obj = ttk.Button(frame_controles, text="1. Inyectar Tono Objetivo (.wav)", width=30, command=lambda: self.cargar_archivo("Objetivo"))
        self.btn_cargar_obj.grid(row=0, column=0, padx=15, pady=10)

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
        """Construye el lienzo en memoria con estética Dark Studio Mode."""
        self.frame_grafica = ttk.LabelFrame(self.root, text="Matriz de Densidad Espectral de Potencia")
        self.color_fondo = '#1A1A1C'
        
        self.figura = Figure(figsize=(10, 5), dpi=100, facecolor=self.color_fondo)
        self.ax = self.figura.add_subplot(111)
        self.ax.set_facecolor(self.color_fondo) 
        
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.frame_grafica)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def mostrar_creditos(self):
        texto = (
            "TGN Tone Architect v1.1\n\n"
            "Motor de análisis acústico y Tone Match basado en LTI/NAM.\n"
            "Desarrollado para la evaluación determinista de hardware.\n\n"
            "Diseño de Sonido y Código: Max - The Guitar Notebook"
        )
        messagebox.showinfo("Acerca del Sistema", texto)

    def verificar_actualizacion(self):
        version_local = "v1.1"
        url_api = "https://api.github.com/repos/max-garcia/Optimizador_Espectral_DSP/releases/latest"
        try:
            respuesta = requests.get(url_api, timeout=5)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                version_remota = datos.get("tag_name", "Desconocida")
                if version_remota != version_local:
                    messagebox.showinfo("Actualización", f"Versión actual: {version_local}\nNueva versión: {version_remota}\nEjecute 'git pull'.")
                else:
                    messagebox.showinfo("Estado", "El software está en su última versión matemática.")
            else:
                messagebox.showerror("Error HTTP", f"Código inesperado: {respuesta.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Colapso", f"Fallo de conexión: {e}")

    def salir_aplicacion(self):
        if messagebox.askokcancel("Cierre", "¿Confirma la finalización de los procesos?"):
            self.root.quit()
            self.root.destroy()    

    def cargar_archivo(self, tipo):
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
        self.btn_analizar.config(text="Procesando...", state=tk.DISABLED)
        threading.Thread(target=self.ejecutar_matematica_dsp).start()

    def ejecutar_matematica_dsp(self):
        try:
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)
            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj)
            freqs_fnt, psd_fnt = self.motor.calcular_psd_welch(senal_fnt)
            self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_fnt, psd_fnt)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso", str(e)))
            self.root.after(0, lambda: self.btn_analizar.config(text="Calcular Ecuación", state=tk.NORMAL))

    def renderizar_espectro(self, f_obj, p_obj, f_fnt, p_fnt):
        """Dibuja los tensores acústicos aplicando un alto contraste geométrico."""
        self.root.geometry("1000x950")
        self.frame_grafica.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.ax.clear()
        
        color_texto = '#E0E0E0'
        color_rejilla = '#333333'
        
        self.ax.set_facecolor(self.color_fondo)
        
        fuente_titulo = {'family': 'sans-serif', 'color': color_texto, 'size': 13, 'weight': 'bold'}
        fuente_ejes = {'family': 'sans-serif', 'color': color_texto, 'size': 11}
        
        self.ax.set_title("Dominio de la Frecuencia (Resolución Acústica)", fontdict=fuente_titulo, pad=15)
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica", fontdict=fuente_ejes)
        self.ax.set_ylabel("Magnitud (dB)", fontdict=fuente_ejes)
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        
        self.ax.grid(True, which="major", color=color_rejilla, linestyle="-", linewidth=0.8, alpha=0.7)
        self.ax.grid(True, which="minor", color=color_rejilla, linestyle=":", linewidth=0.5, alpha=0.3)
        
        for spine in self.ax.spines.values():
            spine.set_color(color_rejilla)
            spine.set_linewidth(1)
            
        self.ax.tick_params(axis='both', colors=color_texto, labelsize=10)
        
        self.ax.plot(f_obj, p_obj, label="Tono Objetivo (Disco)", color='#00ffcc', alpha=0.85, linewidth=1.8)
        self.ax.plot(f_fnt, p_fnt, label="Tono Analizado (Hardware)", color='#ff00ff', alpha=0.85, linewidth=1.8)
        
        leyenda = self.ax.legend(facecolor=self.color_fondo, edgecolor=color_rejilla, fontsize=10)
        for texto_leyenda in leyenda.get_texts():
            texto_leyenda.set_color(color_texto)
            
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
            
            # 1. Cálculo del vector absoluto del directorio de ejecución
            if getattr(sys, 'frozen', False):
                directorio_base = os.path.dirname(sys.executable)
                if sys.platform == "darwin" and ".app/Contents/MacOS" in directorio_base:
                    directorio_base = os.path.abspath(os.path.join(directorio_base, "../../.."))
            else:
                directorio_base = os.path.abspath(os.path.dirname(__file__))

            # 2. Evaluación de la compuerta criptográfica con ruta absoluta
            ruta_licencia = os.path.join(directorio_base, "licencia.key")

            if not os.path.exists(ruta_licencia):
                # Desvío al Modal Comercial
                self.root.after(0, lambda: self.mostrar_ventana_activacion(directorio_base))
                return 
                
            with open(ruta_licencia, "r") as archivo:
                if archivo.read().strip() != hash_esperado:
                    messagebox.showerror("Seguridad", "Firma criptográfica inválida.")
                    return
                    
        except Exception as e:
            messagebox.showerror("Seguridad", f"Colapso en lectura de hardware: {e}")
            return

        # 3. Flujo normal de guardado
        ruta_guardado = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
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

            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)
            
            _, psd_obj = self.motor.calcular_psd_welch(senal_obj)
            _, psd_fnt = self.motor.calcular_psd_welch(senal_fnt)

            vector_ir = self.motor.sintetizar_filtro_fir(psd_obj, psd_fnt, muestras_salida=muestras)
            self.motor.exportar_ir(vector_ir, ruta_guardado, target_sr_export=sr_salida)

            self.root.after(0, lambda: messagebox.showinfo(
                "Síntesis Exitosa", 
                f"Matriz FIR compilada para el ecosistema seleccionado.\n\n"
                f"Longitud: {muestras} muestras\n"
                f"Frecuencia Reloj: {sr_salida} Hz\n"
                f"Destino: {ruta_guardado}"
            ))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso en Síntesis", str(e)))
        finally:
            self.root.after(0, lambda: self.btn_exportar.config(text="Sintetizar Filtro FIR", state=tk.NORMAL))

    def actualizar_progreso(self, valor):
        self.barra_progreso['value'] = valor
        self.lbl_porcentaje.config(text=f"{int(valor)}%")

    def aislar_hilo_busqueda_nam(self):
        if not hasattr(self, 'ruta_objetivo_nam') or not hasattr(self, 'ruta_directorio_nam'):
            messagebox.showerror("Error", "Faltan variables.")
            return
        
        self.btn_buscar_nam.config(text="Escaneando... (Espere)", state=tk.DISABLED)
        self.lbl_resultado_nam.config(text="Calculando ...")
        
        self.barra_progreso['value'] = 0
        self.lbl_porcentaje.config(text="0%")
        
        threading.Thread(target=self.ejecutar_busqueda_dsp).start()

    def ejecutar_busqueda_dsp(self):
        try:
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo_nam)
            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj)
            senal_di, _ = self.motor.cargar_audio(self.ruta_di_nam)

            archivos_nam = [f for f in os.listdir(self.ruta_directorio_nam) if f.endswith('.nam')]
            
            banco_irs = {}
            if hasattr(self, 'ruta_directorio_ir'):
                for arch_ir in [f for f in os.listdir(self.ruta_directorio_ir) if f.endswith('.wav')]:
                    banco_irs[arch_ir] = self.motor.cargar_ir_referencia(os.path.join(self.ruta_directorio_ir, arch_ir))
            else:
                import numpy as np
                banco_irs["Bypass_Directo"] = np.array([1.0])

            menor_mse = float('inf')
            amp_ganador = None
            ir_ganador = None
            psd_ganador = None
            
            total_iteraciones = len(archivos_nam) * len(banco_irs)
            iteracion_actual = 0

            for nombre_nam in archivos_nam:
                try:
                    senal_amp = self.motor.inferencia_neuronal_nam(os.path.join(self.ruta_directorio_nam, nombre_nam), senal_di)

                    for nombre_ir, vector_ir in banco_irs.items():
                        senal_final = senal_amp if nombre_ir == "Bypass_Directo" else self.motor.aplicar_gabinete_referencia(senal_amp, vector_ir)
                        _, psd_test = self.motor.calcular_psd_welch(senal_final)
                        mse_actual = self.motor.calcular_mse_espectral(psd_obj, psd_test)

                        if mse_actual < menor_mse:
                            menor_mse = mse_actual
                            amp_ganador = nombre_nam
                            ir_ganador = nombre_ir
                            psd_ganador = psd_test

                        iteracion_actual += 1
                        progreso = (iteracion_actual / total_iteraciones) * 100
                        self.root.after(0, lambda p=progreso: self.actualizar_progreso(p))
                        
                except Exception as e:
                    print(f"Error procesando el tensor {nombre_nam}: {e}")

            if amp_ganador:
                nivel = self.var_tolerancia.get()
                umbral = 5.0 if "Perfección" in nivel else 15.0 if "Aceptable" in nivel else 30.0
                if menor_mse <= umbral:
                    texto_final = f"Amplificador (.nam): {amp_ganador}\nIR: {ir_ganador}"
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_final, foreground="#00ffcc"))
                    self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_obj, psd_ganador)
                else:
                    texto_fallo = f"Rechazado. MSE: {menor_mse:.2f}\nSupera el umbral topológico."
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_fallo, foreground="red"))
            else:
                self.root.after(0, lambda: self.lbl_resultado_nam.config(text="Fallo: Matriz vacía.", foreground="red"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso Analítico", str(e)))
        finally:
            self.root.after(0, lambda: self.btn_buscar_nam.config(text="Ejecutar Matriz Combinatoria", state=tk.NORMAL))
   
    def construir_firma_ingenieria(self):
        """Construye el bloque inferior de la interfaz con los controles globales."""
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
        """Purga las variables de estado y limpia la matriz visual."""
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
        
        self.lbl_resultado_nam.config(text="Estado: Esperando tensores...", foreground="") 
        
        self.btn_cargar_obj.config(text="1. Inyectar Tono Objetivo (.wav)")
        self.btn_cargar_fnt.config(text="2. Inyectar Tono Grabado (.wav)")
        
        self.frame_grafica.pack_forget()
        self.ax.clear()
        self.root.geometry("1000x420")       
        
        self.barra_progreso['value'] = 0
        self.lbl_porcentaje.config(text="0%") 

    def mostrar_ventana_activacion(self, directorio_base):
        """Renderiza la topología de la compuerta comercial para inyectar la llave."""
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

        # Hardware ID: Uso estricto de tipografía matemática
        frame_hwid = ttk.Frame(frame_interno)
        frame_hwid.pack(fill=tk.X, pady=5)
        ttk.Label(frame_hwid, text="Hardware ID:", font=('SF Pro Display', 12, 'bold')).pack(side=tk.LEFT)
        
        entrada_hwid = ttk.Entry(frame_hwid, font=('Times New Roman', 13))
        entrada_hwid.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        entrada_hwid.insert(0, serial_cliente)
        entrada_hwid.config(state='readonly') 

        # Hash Hexadecimal: Uso estricto de tipografía matemática
        frame_llave = ttk.Frame(frame_interno)
        frame_llave.pack(fill=tk.X, pady=15)
        ttk.Label(frame_llave, text="Llave de Acceso:", font=('SF Pro Display', 12, 'bold')).pack(side=tk.LEFT)
        
        entrada_llave = ttk.Entry(frame_llave, font=('Times New Roman', 13))
        entrada_llave.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        def validar_e_inyectar():
            llave_ingresada = entrada_llave.get().strip()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_cliente)
            
            if llave_ingresada == hash_esperado:
                ruta_licencia = os.path.join(directorio_base, "licencia.key")
                try:
                    with open(ruta_licencia, "w") as archivo:
                        archivo.write(llave_ingresada)
                    messagebox.showinfo("Éxito", "Criptografía validada. El Optimizador Espectral está completamente operativo.", parent=ventana_act)
                    ventana_act.destroy()
                except Exception as e:
                    messagebox.showerror("Error de E/S", f"No se pudo escribir el archivo: {e}", parent=ventana_act)
            else:
                messagebox.showerror("Rechazado", "La llave criptográfica no corresponde a este Hardware ID.", parent=ventana_act)

        btn_activar = ttk.Button(frame_interno, text="Activar Software", command=validar_e_inyectar)
        btn_activar.pack(pady=10)

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