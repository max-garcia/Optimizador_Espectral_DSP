import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# Importación estricta del núcleo matemático (Fase 1)
from motor_dsp import MotorTonalDSP

class OptimizadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizador Espectral DSP - Ingeniería Acústica")
        self.root.geometry("1000x800")
        
        # Instancia del núcleo matemático
        self.motor = MotorTonalDSP()

        # --- TOPOLOGÍA BIMODAL (Pestañas) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)

        self.tab_nam = ttk.Frame(self.notebook)
        self.tab_hardware = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_nam, text="Rama A: Búsqueda Correlacional (NAM)")
        self.notebook.add(self.tab_hardware, text="Rama B: Síntesis Hardware (Filtros FIR)")

        # --- CONSTRUCCIÓN DE LA RAMA B ---
        self.construir_rama_hardware()

        # --- LIENZO CARTESIANO (Matplotlib) ---
        self.construir_lienzo_espectral()

    def construir_rama_hardware(self):
        """Renderiza los selectores topológicos y botones de la Rama B."""
        frame_controles = ttk.Frame(self.tab_hardware)
        frame_controles.pack(fill=tk.X, padx=20, pady=20)

        # Botones de inyección de tensores
        self.btn_cargar_obj = ttk.Button(frame_controles, text="1. Inyectar Tono Objetivo (.wav)", command=lambda: self.cargar_archivo("Objetivo"))
        self.btn_cargar_obj.grid(row=0, column=0, padx=10, pady=5)

        self.btn_cargar_fnt = ttk.Button(frame_controles, text="2. Inyectar Tono Grabado (.wav)", command=lambda: self.cargar_archivo("Fuente"))
        self.btn_cargar_fnt.grid(row=0, column=1, padx=10, pady=5)

        # Selector de ecosistema comercial
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

        # Botones de ejecución algorítmica
        self.btn_analizar = ttk.Button(frame_controles, text="Calcular Ecuación Espectral", command=self.aislar_hilo_analisis)
        self.btn_analizar.grid(row=2, column=0, padx=10, pady=10)

        self.btn_exportar = ttk.Button(frame_controles, text="Sintetizar Filtro FIR", command=self.aislar_hilo_sintesis)
        self.btn_exportar.grid(row=2, column=1, padx=10, pady=10)

    def construir_lienzo_espectral(self):
        """Acopla el motor gráfico de Matplotlib a la ventana de Tkinter."""
        frame_grafica = ttk.LabelFrame(self.root, text="Matriz de Densidad Espectral de Potencia")
        frame_grafica.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.figura = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figura.add_subplot(111)
        
        # Definición estricta de las escalas acústicas
        self.ax.set_title("Dominio de la Frecuencia")
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica")
        self.ax.set_ylabel("Magnitud (dB)")
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        self.ax.grid(True, which="both", ls="--", alpha=0.4)

        # Inyección del render en el marco
        self.canvas = FigureCanvasTkAgg(self.figura, master=frame_grafica)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# --- FUNCIONES DE ENRUTAMIENTO Y CONCURRENCIA ---

    def cargar_archivo(self, tipo):
        """Abre el explorador de macOS para inyectar el tensor de audio."""
        ruta = filedialog.askopenfilename(title=f"Seleccionar Tono {tipo}", filetypes=[("Archivos de Audio", "*.wav")])
        if ruta:
            if tipo == "Objetivo":
                self.ruta_objetivo = ruta
                self.btn_cargar_obj.config(text="1. Tono Objetivo Inyectado ✓")
            else:
                self.ruta_fuente = ruta
                self.btn_cargar_fnt.config(text="2. Tono Grabado Inyectado ✓")

    def aislar_hilo_analisis(self):
        """Compulsa de seguridad. Verifica que existan ambos tensores antes de calcular."""
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan variables en la ecuación. Inyecte ambos archivos .wav.")
            return

        # Bloqueamos el botón para evitar que el usuario lance 2 cálculos simultáneos
        self.btn_analizar.config(text="Procesando Matrices FFT...", state=tk.DISABLED)
        
        # Desacoplamos la matemática de la interfaz gráfica (Multithreading)
        hilo = threading.Thread(target=self.ejecutar_matematica_dsp)
        hilo.start()

    def ejecutar_matematica_dsp(self):
        """Este método corre en un núcleo de CPU separado. Calcula Welch de forma invisible."""
        try:
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)

            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj)
            freqs_fnt, psd_fnt = self.motor.calcular_psd_welch(senal_fnt)

            # Una vez resuelta la ecuación, enviamos los datos de vuelta al hilo principal para graficar
            self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_fnt, psd_fnt)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso en Motor DSP", str(e)))
            self.root.after(0, lambda: self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL))

    def renderizar_espectro(self, f_obj, p_obj, f_fnt, p_fnt):
        """Dibuja los tensores en el plano cartesiano usando Matplotlib."""
        self.ax.clear()
        self.ax.set_title("Dominio de la Frecuencia (Resolución Acústica)")
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica")
        self.ax.set_ylabel("Magnitud (dB)")
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        self.ax.grid(True, which="both", ls="--", alpha=0.4)

        # Gráfica superpuesta de ambas curvas
        self.ax.plot(f_obj, p_obj, label="Tono Objetivo (Disco)", color='#00ffcc', alpha=0.8, linewidth=1.5)
        self.ax.plot(f_fnt, p_fnt, label="Tono Fuente (Pedalera)", color='#ff00ff', alpha=0.8, linewidth=1.5)
        self.ax.legend()

        self.canvas.draw()
        
        # Liberamos el botón
        self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL)

    def aislar_hilo_sintesis(self):
        """Prepara el entorno y pide la ruta de guardado en el hilo principal de macOS."""
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan las matrices de audio. Inyecte ambos archivos primero.")
            return

        # Pedir al usuario dónde guardar el archivo ANTES de congelar el hilo
        ruta_guardado = filedialog.asksaveasfilename(
            title="Exportar Filtro FIR de Fase Mínima",
            defaultextension=".wav",
            filetypes=[("Archivo de Audio WAV", "*.wav")]
        )
        
        if not ruta_guardado:
            return # El usuario canceló la operación

        self.btn_exportar.config(text="Sintetizando Tensor...", state=tk.DISABLED)
        
        # Extraer la selección del hardware (Line 6, Fractal, Kemper)
        seleccion_hw = self.variable_hardware.get()
        
        # Desacoplar el cálculo Cepstral hacia un núcleo secundario
        hilo = threading.Thread(target=self.ejecutar_sintesis_dsp, args=(ruta_guardado, seleccion_hw))
        hilo.start()

    def ejecutar_sintesis_dsp(self, ruta_guardado, seleccion_hw):
        """Calcula la Transformada de Hilbert y compila el binario .wav."""
        try:
            # 1. Enrutamiento de parámetros matemáticos exigidos por la industria
            muestras = 1024
            sr_salida = 48000
            
            if "Fractal" in seleccion_hw:
                muestras = 2048
            elif "Kemper" in seleccion_hw:
                muestras = 2048
                sr_salida = 44100 # Exige remuestreo (Downsampling)

            # 2. Ingesta estricta de las matrices
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo)
            senal_fnt, _ = self.motor.cargar_audio(self.ruta_fuente)
            
            _, psd_obj = self.motor.calcular_psd_welch(senal_obj)
            _, psd_fnt = self.motor.calcular_psd_welch(senal_fnt)

            # 3. Resolución de la ecuación (Fase Mínima)
            vector_ir = self.motor.sintetizar_filtro_fir(psd_obj, psd_fnt, muestras_salida=muestras)
            
            # 4. Escritura en disco (PCM 24-bit)
            self.motor.exportar_ir(vector_ir, ruta_guardado, target_sr_export=sr_salida)

            # 5. Notificación de éxito retornada al hilo principal
            self.root.after(0, lambda: messagebox.showinfo(
                "Éxito Matemático", 
                f"Filtro FIR compilado exitosamente.\n\nLongitud: {muestras} muestras\nFrecuencia: {sr_salida} Hz\nDestino: {ruta_guardado}"
            ))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Colapso en Síntesis", str(e)))
        finally:
            # Restaurar el botón independientemente del resultado
            self.root.after(0, lambda: self.btn_exportar.config(text="Sintetizar Filtro FIR", state=tk.NORMAL))

# Bloque de inicialización estricta
if __name__ == "__main__":
    raiz = tk.Tk()
    
    # Inyección del tema nativo para acoplamiento estético en macOS
    style = ttk.Style()
    if 'aqua' in style.theme_names():
        style.theme_use('aqua') 
        
    app = OptimizadorGUI(raiz)
    raiz.mainloop()