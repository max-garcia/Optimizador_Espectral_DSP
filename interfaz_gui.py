import tkinter as tk
import os
from tkinter import filedialog, messagebox
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# Importación estricta del núcleo matemático (Fase 1)
from motor_dsp import MotorTonalDSP
from gestor_licencias import CriptografiaHWID  

class OptimizadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizador Espectral DSP - Ingeniería Acústica")
        self.root.geometry("1000x350")
        
        # Instancia del núcleo matemático
        self.motor = MotorTonalDSP()

        # Instancia del núcleo matemático
        self.motor = MotorTonalDSP()
        # Instancia del motor criptográfico (Candado de Hardware)
        self.seguridad = CriptografiaHWID()

        # --- TOPOLOGÍA BIMODAL (Pestañas) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)

        self.tab_nam = ttk.Frame(self.notebook)
        self.tab_hardware = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_nam, text="Rama A: Búsqueda Correlacional (NAM)")
        self.notebook.add(self.tab_hardware, text="Rama B: Síntesis Hardware (Filtros FIR)")

        # Variable de estado para el motor de escaneo (Por defecto: Solo IRs)
        self.modo_escaneo = tk.StringVar(value="IR")

        # --- CONSTRUCCIÓN DE LA RAMA A ---
        self.construir_rama_nam()

        # --- CONSTRUCCIÓN DE LA RAMA B ---
        self.construir_rama_hardware()

        # --- LIENZO CARTESIANO (Matplotlib) ---
        self.construir_lienzo_espectral()

    def construir_rama_nam(self):
        """Renderiza la Rama A con compuertas lógicas de escaneo restrictivo."""
        frame_controles_nam = ttk.Frame(self.tab_nam)
        frame_controles_nam.pack(fill=tk.X, padx=20, pady=20)

        # Fila 0: Inyección de Tensores
        self.btn_cargar_obj_nam = ttk.Button(frame_controles_nam, text="1. Tono Objetivo (.wav)", command=lambda: self.cargar_archivo("Objetivo_NAM"))
        self.btn_cargar_obj_nam.grid(row=0, column=0, padx=10, pady=5)

        self.btn_cargar_di_nam = ttk.Button(frame_controles_nam, text="2. Tono DI Limpio (.wav)", command=lambda: self.cargar_archivo("DI_NAM"))
        self.btn_cargar_di_nam.grid(row=0, column=1, padx=10, pady=5)

        # Fila 1: Compuertas Lógicas de Escaneo (Radiobuttons)
        frame_radios = ttk.LabelFrame(frame_controles_nam, text="Motor de Análisis Acústico")
        frame_radios.grid(row=1, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E, padx=10)

        ttk.Radiobutton(frame_radios, text="Solo Gabinetes/IRs (.wav)", variable=self.modo_escaneo, value="IR").pack(side=tk.LEFT, padx=15, pady=5)
        ttk.Radiobutton(frame_radios, text="Solo Amplificadores (.nam)", variable=self.modo_escaneo, value="NAM").pack(side=tk.LEFT, padx=15, pady=5)
        ttk.Radiobutton(frame_radios, text="Ecosistema Híbrido (Ambos)", variable=self.modo_escaneo, value="AMBOS").pack(side=tk.LEFT, padx=15, pady=5)

        # Fila 2: Carpeta y Tolerancia
        self.btn_cargar_dir_nam = ttk.Button(frame_controles_nam, text="3. Carpeta de Escaneo", command=self.seleccionar_directorio_nam)
        self.btn_cargar_dir_nam.grid(row=2, column=0, padx=10, pady=10)

        self.var_tolerancia = tk.StringVar()
        self.selector_tolerancia = ttk.Combobox(frame_controles_nam, textvariable=self.var_tolerancia, state="readonly", width=25)
        self.selector_tolerancia['values'] = ("Perfección (MSE < 5.0)", "Aceptable (MSE < 15.0)", "Cercano (MSE < 30.0)", "Sin Filtro")
        self.selector_tolerancia.current(1)
        self.selector_tolerancia.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)

        # Fila 3 y 4: Ejecución y Resultados
        self.btn_buscar_nam = ttk.Button(frame_controles_nam, text="Ejecutar Escaneo Espectral", command=self.aislar_hilo_busqueda_nam)
        self.btn_buscar_nam.grid(row=3, column=0, columnspan=2, pady=15)

        self.lbl_resultado_nam = ttk.Label(frame_controles_nam, text="Estado: Esperando matrices...", font=('Helvetica', 12, 'bold'))
        self.lbl_resultado_nam.grid(row=4, column=0, columnspan=2, pady=5)

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
        """Construye el lienzo en memoria, pero lo mantiene invisible (Divulgación Progresiva)."""
        self.frame_grafica = ttk.LabelFrame(self.root, text="Matriz de Densidad Espectral de Potencia")
        
        self.figura = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figura.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.frame_grafica)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# --- FUNCIONES DE ENRUTAMIENTO Y CONCURRENCIA ---

    def cargar_archivo(self, tipo):
        """Abre el explorador de macOS para inyectar el tensor de audio correspondiente."""
        ruta = filedialog.askopenfilename(title=f"Seleccionar Tono {tipo}", filetypes=[("Archivos de Audio", "*.wav")])
        if ruta:
            # Enrutamiento de la Rama B (Síntesis FIR)
            if tipo == "Objetivo":
                self.ruta_objetivo = ruta
                self.btn_cargar_obj.config(text="1. Tono Objetivo Inyectado ✓")
            elif tipo == "Fuente":
                self.ruta_fuente = ruta
                self.btn_cargar_fnt.config(text="2. Tono Grabado Inyectado ✓")
                
            # Enrutamiento de la Rama A (Inferencia LTI y Neuronal NAM)
            elif tipo == "Objetivo_NAM":
                self.ruta_objetivo_nam = ruta
                self.btn_cargar_obj_nam.config(text="1. Tono Objetivo Inyectado ✓")
            elif tipo == "DI_NAM":
                self.ruta_di_nam = ruta
                self.btn_cargar_di_nam.config(text="2. Tono DI Limpio Inyectado ✓")

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
        """Expande la geometría de la ventana, revela el contenedor y dibuja los tensores."""
        # Mutación dinámica: Expansión vertical a 850 píxeles
        self.root.geometry("1000x850")
        
        self.frame_grafica.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.ax.clear()
        # ... (el resto del código se mantiene idéntico)
        
        self.ax.clear()
        self.ax.set_title("Dominio de la Frecuencia (Resolución Acústica)")
        self.ax.set_xlabel("Frecuencia (Hz) - Escala Logarítmica")
        self.ax.set_ylabel("Magnitud (dB)")
        self.ax.set_xscale('log')
        self.ax.set_xlim([20, 20000])
        self.ax.grid(True, which="both", ls="--", alpha=0.4)

        self.ax.plot(f_obj, p_obj, label="Tono Objetivo (Disco)", color='#00ffcc', alpha=0.8, linewidth=1.5)
        self.ax.plot(f_fnt, p_fnt, label="Tono Analizado", color='#ff00ff', alpha=0.8, linewidth=1.5)
        self.ax.legend()

        self.canvas.draw()
        
        # Liberamos el botón
        self.btn_analizar.config(text="Calcular Ecuación Espectral", state=tk.NORMAL)

    def aislar_hilo_sintesis(self):
        """Compulsa de seguridad criptográfica y preparación del entorno de síntesis."""
        if not hasattr(self, 'ruta_objetivo') or not hasattr(self, 'ruta_fuente'):
            messagebox.showerror("Error Topológico", "Faltan las matrices de audio. Inyecte ambos archivos primero.")
            return

        # --- BLOQUE DE SEGURIDAD ESTRICTA (HWID) ---
        try:
            # 1. Extracción del vector de hardware
            serial_fisico = self.seguridad.extraer_hardware_serial()
            hash_esperado = self.seguridad.generar_llave_maestra(serial_fisico)
            
            # 2. Verificación de existencia del archivo físico
            ruta_licencia = "licencia.key"
            if not os.path.exists(ruta_licencia):
                mensaje_bloqueo = (
                    "ACCESO DENEGADO (Modo Freemium)\n\n"
                    "La síntesis de hardware está bloqueada.\n"
                    f"HWID de su equipo: {serial_fisico}\n\n"
                    "Contacte al desarrollador para adquirir su llave matemática."
                )
                messagebox.showwarning("Licencia Requerida", mensaje_bloqueo)
                return # Abortar ejecución
                
            # 3. Verificación de integridad criptográfica
            with open(ruta_licencia, "r") as archivo:
                llave_usuario = archivo.read().strip()
                
            if llave_usuario != hash_esperado:
                messagebox.showerror("Violación de Seguridad", "La licencia detectada es inválida o no corresponde a este hardware.")
                return # Abortar ejecución
                
        except Exception as e:
            messagebox.showerror("Fallo en Módulo de Seguridad", f"Error al verificar la topología del hardware: {e}")
            return
        # --- FIN DEL BLOQUE DE SEGURIDAD ---

        # Si el código llega aquí, la matemática validó al usuario. Se procede con la exportación.
        ruta_guardado = filedialog.asksaveasfilename(
            title="Exportar Filtro FIR de Fase Mínima",
            defaultextension=".wav",
            filetypes=[("Archivo de Audio WAV", "*.wav")]
        )
        
        if not ruta_guardado:
            return

        self.btn_exportar.config(text="Sintetizando Tensor...", state=tk.DISABLED)
        seleccion_hw = self.variable_hardware.get()
        
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

    def seleccionar_directorio_nam(self):
        """Abre el explorador de macOS para seleccionar la carpeta con cientos de IRs."""
        ruta_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Búsqueda")
        if ruta_dir:
            self.ruta_directorio_nam = ruta_dir
            self.btn_cargar_dir_nam.config(text="2. Carpeta Inyectada ✓")

    # Necesitamos modificar levemente cargar_archivo para que acepte el nuevo tipo
    def cargar_archivo(self, tipo):
        """Abre el explorador y muta el estado visual del botón."""
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
            elif tipo == "DI_NAM": # <--- Esta es la compuerta exacta
                self.ruta_di_nam = ruta
                self.btn_cargar_di_nam.config(text="2. DI Limpio Inyectado ✓")

    def aislar_hilo_busqueda_nam(self):
        """Bloquea la interfaz y lanza el escáner iterativo en un núcleo secundario."""
        if not hasattr(self, 'ruta_objetivo_nam') or not hasattr(self, 'ruta_directorio_nam'):
            messagebox.showerror("Error Topológico", "Faltan variables. Inyecte el objetivo y la carpeta.")
            return

        self.btn_buscar_nam.config(text="Escaneando Matrices... (Espere)", state=tk.DISABLED)
        self.lbl_resultado_nam.config(text="Analizando entropía de la carpeta...")
        
        hilo_nam = threading.Thread(target=self.ejecutar_busqueda_dsp)
        hilo_nam.start()

    def ejecutar_busqueda_dsp(self):
        """
        Itera sobre el directorio acotado, calcula inferencias neuronales o LTI según 
        la topología seleccionada, resuelve el MSE espectral y aplica la compuerta de tolerancia matemática.
        """
        import os
        try:
            # 1. Resolución estricta de la matriz del Tono Objetivo
            senal_obj, _ = self.motor.cargar_audio(self.ruta_objetivo_nam)
            freqs_obj, psd_obj = self.motor.calcular_psd_welch(senal_obj)

            mejor_archivo = None
            menor_mse = float('inf')
            psd_ganador = None

            # 2. Lectura de variables de estado de la interfaz
            modo_seleccionado = self.modo_escaneo.get()
            archivos = os.listdir(self.ruta_directorio_nam)

            # Precarga condicional de la señal de excitación (DI) para inferencia
            senal_di = None
            if hasattr(self, 'ruta_di_nam'):
                senal_di, _ = self.motor.cargar_audio(self.ruta_di_nam)

            # 3. Bucle Iterativo sobre el tensor de archivos
            for nombre_archivo in archivos:
                ext = nombre_archivo.lower()
                ruta_completa = os.path.join(self.ruta_directorio_nam, nombre_archivo)

                try:
                    # Compuerta lógica para sistemas Lineales (Gabinetes/IRs .wav)
                    if ext.endswith(".wav") and modo_seleccionado in ["IR", "AMBOS"]:
                        senal_test, _ = self.motor.cargar_audio(ruta_completa)
                        freqs_test, psd_test = self.motor.calcular_psd_welch(senal_test)

                    # Compuerta lógica para inferencia no lineal (Modelos NAM .nam)
                    elif ext.endswith(".nam") and modo_seleccionado in ["NAM", "AMBOS"]:
                        if senal_di is None:
                            self.root.after(0, lambda: messagebox.showerror("Colapso Topológico", "Falta Tono DI Limpio. Es matemáticamente imposible excitar una red neuronal sin señal de entrada."))
                            return

                        # Notificación asíncrona a la interfaz para modelos pesados
                        self.root.after(0, lambda n=nombre_archivo: self.lbl_resultado_nam.config(text=f"Infiriendo red neuronal: {n}..."))
                        
                        senal_test = self.motor.inferencia_neuronal_nam(ruta_completa, senal_di)
                        freqs_test, psd_test = self.motor.calcular_psd_welch(senal_test)

                    else:
                        # Archivo descartado por el filtro booleano del usuario o formato inválido
                        continue

                    # 4. Cálculo de Distancia Euclidiana (MSE)
                    mse_actual = self.motor.calcular_mse_espectral(psd_obj, psd_test)

                    if mse_actual < menor_mse:
                        menor_mse = mse_actual
                        mejor_archivo = nombre_archivo
                        psd_ganador = psd_test

                except Exception as e:
                    # Se omite silenciosamente el archivo corrupto para no frenar la iteración de la carpeta
                    print(f"Error procesando matriz {nombre_archivo}: {e}")
                    continue

            # 5. Evaluación de la Compuerta de Tolerancia (Quality Gate)
            if mejor_archivo:
                nivel_texto = self.var_tolerancia.get()
                if "Perfección" in nivel_texto:
                    umbral_maximo = 5.0
                elif "Aceptable" in nivel_texto:
                    umbral_maximo = 15.0
                elif "Cercano" in nivel_texto:
                    umbral_maximo = 30.0
                else:
                    umbral_maximo = float('inf')

                # Aplicación de la inecuación de calidad
                if menor_mse <= umbral_maximo:
                    texto_exito = f"Éxito: {mejor_archivo} (MSE: {menor_mse:.4f})"
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_exito, foreground="green"))
                    self.root.after(0, self.renderizar_espectro, freqs_obj, psd_obj, freqs_obj, psd_ganador)
                else:
                    texto_fallo = f"Rechazado. El mejor (MSE: {menor_mse:.2f}) superó su límite de tolerancia."
                    self.root.after(0, lambda: self.lbl_resultado_nam.config(text=texto_fallo, foreground="red"))
                    self.root.after(0, self.frame_grafica.pack_forget)
                    self.root.after(0, lambda: self.root.geometry("1000x350"))
            else:
                self.root.after(0, lambda: self.lbl_resultado_nam.config(text="Error: No se encontraron matrices compatibles en el escaneo.", foreground="red"))

        except Exception as e:
            # Captura de colapsos críticos fuera del bucle
            self.root.after(0, lambda: messagebox.showerror("Colapso en Escaneo Espectral", str(e)))
            
        finally:
            # 6. Liberación estricta del hilo principal y restauración del botón
            self.root.after(0, lambda: self.btn_buscar_nam.config(text="Ejecutar Escaneo Espectral", state=tk.NORMAL))

# Bloque de inicialización estricta
if __name__ == "__main__":
    raiz = tk.Tk()
    
    # Inyección del tema nativo para acoplamiento estético en macOS
    style = ttk.Style()
    if 'aqua' in style.theme_names():
        style.theme_use('aqua') 
        
    app = OptimizadorGUI(raiz)
    raiz.mainloop()