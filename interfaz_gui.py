import tkinter as tk
import os
from tkinter import filedialog, messagebox
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import requests

# Importación estricta del núcleo matemático (Fase 1)
from motor_dsp import MotorTonalDSP
from gestor_licencias import CriptografiaHWID  

class OptimizadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizador Espectral DSP - Ingeniería Acústica")
        self.root.geometry("1000x350")
        
        # Instancia del núcleo matemático y criptográfico
        self.motor = MotorTonalDSP()
        self.seguridad = CriptografiaHWID()

        # 1. INYECCIÓN DEL MENÚ LOCAL (Antes del Notebook)
        self.construir_barra_menu()

        # 2. TOPOLOGÍA BIMODAL (Pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)

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

    def construir_barra_menu(self):
        """
        Construye una barra de menú local forzada dentro de la ventana principal.
        Evita la proyección a la barra global de macOS.
        """
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
        frame_controles_nam = ttk.Frame(self.tab_nam)
        frame_controles_nam.pack(fill=tk.X, padx=20, pady=20)

        self.btn_cargar_obj_nam = ttk.Button(frame_controles_nam, text="1. Tono Objetivo (.wav)", command=lambda: self.cargar_archivo("Objetivo_NAM"))
        self.btn_cargar_obj_nam.grid(row=0, column=0, padx=10, pady=5)

        self.btn_cargar_di_nam = ttk.Button(frame_controles_nam, text="2. Tono DI Limpio (.wav)", command=lambda: self.cargar_archivo("DI_NAM"))
        self.btn_cargar_di_nam.grid(row=0, column=1, padx=10, pady=5)

        self.btn_cargar_dir_nam = ttk.Button(frame_controles_nam, text="3. Carpeta Cabezales (.nam)", command=self.seleccionar_directorio_nam)
        self.btn_cargar_dir_nam.grid(row=1, column=0, padx=10, pady=15)

        self.btn_cargar_dir_ir = ttk.Button(frame_controles_nam, text="4. Carpeta Gabinetes IR (.wav)", command=self.seleccionar_directorio_ir)
        self.btn_cargar_dir_ir.grid(row=1, column=1, padx=10, pady=15)

        self.var_tolerancia = tk.StringVar()
        self.selector_tolerancia = ttk.Combobox(frame_controles_nam, textvariable=self.var_tolerancia, state="readonly", width=35)
        self.selector_tolerancia['values'] = ("Perfección Topológica (MSE < 5.0)", "Aceptable Comercial (MSE < 15.0)", "Aproximación (MSE < 30.0)")
        self.selector_tolerancia.current(1)
        self.selector_tolerancia.grid(row=2, column=0, columnspan=2, pady=5)

        self.btn_buscar_nam = ttk.Button(frame_controles_nam, text="Ejecutar Matriz Combinatoria", command=self.aislar_hilo_busqueda_nam)
        self.btn_buscar_nam.grid(row=3, column=0, columnspan=2, pady=15)

        self.lbl_resultado_nam = ttk.Label(frame_controles_nam, text="Estado: Esperando tensores...", font=('Helvetica', 12, 'bold'))
        self.lbl_resultado_nam.grid(row=4, column=0, columnspan=2, pady=5)

    def construir_rama_hardware(self):
        frame_controles = ttk.Frame(self.tab_hardware)
        frame_controles.pack(fill=tk.X, padx=20, pady=20)

        self.btn_cargar_obj = ttk.Button(frame_controles, text="1. Inyectar Tono Objetivo (.wav)", command=lambda: self.cargar_archivo("Objetivo"))
        self.btn_cargar_obj.grid(row=0, column=0, padx=10, pady=5)

        self.btn_cargar_fnt = ttk.Button(frame_controles, text="2. Inyectar Tono Grabado (.wav)", command=lambda: self.cargar_archivo("Fuente"))
        self.btn_cargar_fnt.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame_controles, text="3. Ecosistema de Exportación:").grid(row=1, column=0, sticky=tk.E, padx=10, pady=15)
        
        self.variable_hardware = tk.StringVar()
        self.selector_hardware = ttk.Combobox(frame_controles, textvariable=self.variable_hardware, state="readonly", width=35)
        self.selector_hardware['values'] = (
            "Line 6 (1024 muestras | 48 kHz)",
            "Fractal Audio (2048 muestras | 48 kHz)",
            "Kemper Profiler (2048 muestras | 44.1 kHz)"
        )
        self.selector_hardware.current(0)
        self.selector_hardware.grid(row=1, column=1, sticky=tk.W, padx=10, pady=15)

        self.btn_analizar = ttk.Button(frame_controles, text="Calcular Ecuación Espectral", command=self.aislar_hilo_analisis)
        self.btn_analizar.grid(row=2, column=0, padx=10, pady=10)

        self.btn_exportar = ttk.Button(frame_controles, text="Sintetizar Filtro FIR", command=self.aislar_hilo_sintesis)
        self.btn_exportar.grid(row=2, column=1, padx=10, pady=10)

    def construir_lienzo_espectral(self):
        self.frame_grafica = ttk.LabelFrame(self.root, text="Matriz de Densidad Espectral de Potencia")
        self.figura = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figura.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.frame_grafica)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def mostrar_creditos(self):
        texto = (
            "Optimizador Espectral DSP v1.0\n\n"
            "Motor de análisis acústico y Tone Match basado en LTI/NAM.\n"
            "Desarrollado para la evaluación determinista de hardware.\n\n"
            "Diseño de Sonido y Código: Max - The Guitar Notebook"
        )
        messagebox.showinfo("Acerca del Sistema", texto)

    def verificar_actualizacion(self):
        version_local = "v1.0"
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
        self.root.geometry("1000x850")
        self.frame_grafica.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.ax.clear()
        self.ax.set_title("Dominio de la Frecuencia (Resolución Acústica)")
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica")
        self.ax.set_ylabel("Magnitud (dB)")
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        self.ax.grid(True, which="both", ls="--", alpha=0.4)
        self.ax.plot(f_obj, p_obj, label="Tono Objetivo", color='#00ffcc', alpha=0.8, linewidth=1.5)
        self.ax.plot(f_fnt, p_fnt, label="Tono Analizado", color='#ff00ff', alpha=0.8, linewidth=1.5)
        self.ax.legend()
        self.canvas.draw()
        if hasattr(self, 'btn_analizar'):
            self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL)

    def aislar_hilo_sintesis(self):
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error", "Faltan las matrices de audio.")
            return
        try:
            serial_fisico = self.seguridad.extraer_hardware_serial()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_fisico)
            if not os.path.exists("licencia.key"):
                messagebox.showwarning("Bloqueo", "Síntesis bloqueada. Requiere licencia.")
                return 
            with open("licencia.key", "r") as archivo:
                if archivo.read().strip() != hash_esperado:
                    messagebox.showerror("Seguridad", "Licencia inválida.")
                    return 
        except Exception as e:
            messagebox.showerror("Seguridad", f"Error de hardware: {e}")
            return

        ruta_guardado = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if not ruta_guardado:
            return
        self.btn_exportar.config(text="Sintetizando...", state=tk.DISABLED)
        threading.Thread(target=self.ejecutar_sintesis_dsp, args=(ruta_guardado, self.variable_hardware.get())).start()

    def ejecutar_sintesis_dsp(self, ruta_guardado, seleccion_hw):
        try:
            muestras = 1024
            sr_salida = 48000
            if "Fractal" in seleccion_hw: muestras = 2048
            elif "Kemper" in seleccion_hw: muestras, sr_salida = 2048, 44100
            
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)
            _, psd_obj = self.motor.calcular_psd_welch(senal_obj)
            _, psd_fnt = self.motor.calcular_psd_welch(senal_fnt)
            
            vector_ir = self.motor.sintetizar_filtro_fir(psd_obj, psd_fnt, muestras_salida=muestras)
            self.motor.exportar_ir(vector_ir, ruta_guardado, target_sr_export=sr_salida)
            
            self.root.after(0, lambda: messagebox.showinfo("Éxito", "Filtro FIR compilado."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso", str(e)))
        finally:
            self.root.after(0, lambda: self.btn_exportar.config(text="Sintetizar Filtro FIR", state=tk.NORMAL))

    def aislar_hilo_busqueda_nam(self):
        if not hasattr(self, 'ruta_objetivo_nam') or not hasattr(self, 'ruta_directorio_nam'):
            messagebox.showerror("Error", "Faltan variables.")
            return
        self.btn_buscar_nam.config(text="Escaneando... (Espere)", state=tk.DISABLED)
        self.lbl_resultado_nam.config(text="Analizando entropía...")
        threading.Thread(target=self.ejecutar_busqueda_dsp).start()

    def ejecutar_busqueda_dsp(self):
        import os
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
            mejor_combinacion, psd_ganador = None, None

            for nombre_nam in archivos_nam:
                try:
                    self.root.after(0, lambda n=nombre_nam: self.lbl_resultado_nam.config(text=f"Infiriendo: {n}"))
                    senal_amp = self.motor.inferencia_neuronal_nam(os.path.join(self.ruta_directorio_nam, nombre_nam), senal_di)

                    for nombre_ir, vector_ir in banco_irs.items():
                        senal_final = senal_amp if nombre_ir == "Bypass_Directo" else self.motor.aplicar_gabinete_referencia(senal_amp, vector_ir)
                        _, psd_test = self.motor.calcular_psd_welch(senal_final)
                        mse_actual = self.motor.calcular_mse_espectral(psd_obj, psd_test)

                        if mse_actual < menor_mse:
                            menor_mse = mse_actual
                            mejor_combinacion = f"{nombre_nam} + {nombre_ir}" if nombre_ir != "Bypass_Directo" else nombre_nam
                            psd_ganador = psd_test
                except Exception as e:
                    print(f"Error en {nombre_nam}: {e}")

            if mejor_combinacion:
                nivel = self.var_tolerancia.get()
                umbral = 5.0 if "Perfección" in nivel else 15.0 if "Aceptable" in nivel else 30.0
                if menor_mse <= umbral:
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=f"ÓPTIMO: {mejor_combinacion}\nMSE: {menor_mse:.2f}", foreground="green"))
                    self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_obj, psd_ganador)
                else:
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=f"Rechazado. Mínimo ({menor_mse:.2f}) supera tolerancia.", foreground="red"))
            else:
                self.root.after(0, lambda: self.lbl_resultado_nam.config(text="Fallo: Matriz vacía.", foreground="red"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso", str(e)))
        finally:
            self.root.after(0, lambda: self.btn_buscar_nam.config(text="Ejecutar Matriz Combinatoria", state=tk.NORMAL))

if __name__ == "__main__":
    raiz = tk.Tk()
    style = ttk.Style()
    if 'aqua' in style.theme_names():
        style.theme_use('aqua') 
    app = OptimizadorGUI(raiz)
    raiz.mainloop()