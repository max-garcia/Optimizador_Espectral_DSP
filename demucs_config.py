from enum import Enum
from dataclasses import dataclass
import warnings

# 1. Definición de Espacios Discretos (Enums)
class ComputeDevice(Enum):
    CPU = "cpu"
    CUDA = "cuda"

class TargetStem(Enum):
    ALL = "all"        # Extrae los 4 tensores base
    OTHER = "other"    # Aísla la guitarra/instrumento del resto

class QualityLevel(Enum):
    # Definición matricial: (Etiqueta UI, Shifts, Overlap)
    DRAFT = ("Básico", 1, 0.10)
    STANDARD = ("Estándar", 2, 0.25)
    PRO = ("Pro", 5, 0.50)

    def __init__(self, label: str, shifts: int, overlap: float):
        self.label = label
        self.shifts = shifts
        self.overlap = overlap

# 2. Estructura de Datos y Validación de Axiomas
@dataclass
class DemucsInferenceConfig:
    device: ComputeDevice
    quality: QualityLevel
    stem: TargetStem
    segment_size: int = 40  # L_s: Longitud del bloque en segundos (Default)

    def __post_init__(self):
        """
        Ejecuta la validación del sistema inmediatamente después de la instanciación.
        Aplica el axioma de restricción computacional.
        """
        self._validate_compute_limits()

    def _validate_compute_limits(self):
        # Evaluación de la complejidad asintótica: O(S * T / (1 - alpha))
        # Si el hardware es CPU, prohibimos la evaluación del nivel PRO.
        if self.device == ComputeDevice.CPU and self.quality == QualityLevel.PRO:
            warnings.warn(
                "Advertencia de Costo Computacional: Ejecución en CPU con nivel PRO detectada. "
                "Para evitar un tiempo de ejecución que tiende al infinito y el bloqueo del hilo, "
                "el sistema ha degradado automáticamente el tensor a nivel ESTÁNDAR.",
                RuntimeWarning
            )
            # Degradar parámetros dinámicamente
            self.quality = QualityLevel.STANDARD

    def get_demucs_args(self) -> list:
        """
        Traduce el estado validado a los argumentos exactos requeridos por la CLI de Demucs.
        """
        args = [
            "-d", self.device.value,
            "--shifts", str(self.quality.shifts),
            "--overlap", str(self.quality.overlap),
            "--segment", str(self.segment_size)
        ]
        
        # Ruteo de tensores de salida
        if self.stem == TargetStem.OTHER:
            args.extend(["--two-stems", "other"])
            
        return args
    
import subprocess
import threading
import re
import sys
from typing import Callable, Optional

class DemucsRunner:
    """
    Controlador de ejecución asíncrona para la separación de tensores espectrales.
    Aísla la carga I/O y de CPU/GPU del hilo principal de la aplicación.
    """
    def __init__(self, config: 'DemucsInferenceConfig', input_path: str, output_dir: str):
        self.config = config
        self.input_path = input_path
        self.output_dir = output_dir
        self._process: Optional[subprocess.Popen] = None
        self._is_running = False

    def start_extraction(self, 
                         on_progress: Callable[[float], None], 
                         on_complete: Callable[[int], None], 
                         on_error: Callable[[str], None]):
        """
        Bifurca el hilo principal y comienza la ejecución.
        Los callbacks son inyecciones de dependencias para reportar el estado a la GUI.
        """
        if self._is_running:
            return  # Previene la instanciación matricial redundante

        self._is_running = True
        
        # Instanciamos T_Worker
        worker_thread = threading.Thread(
            target=self._run_subprocess,
            args=(on_progress, on_complete, on_error),
            daemon=True # El hilo muere si se cierra la ventana principal
        )
        worker_thread.start()

    def _run_subprocess(self, on_progress, on_complete, on_error):
        """
        Lógica interna del hilo secundario. Ejecuta el binario y parsea stdout.
        """
        # 1. Construcción del vector de argumentos del sistema
        # Se asume que demucs es ejecutable globalmente en el PATH del entorno python
        cmd = ["demucs", self.input_path, "-o", self.output_dir]
        cmd.extend(self.config.get_demucs_args())

        try:
            # 2. Invocación del proceso del sistema operativo
            # Redirigimos stdout y stderr para capturar el progreso del tensor
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Demucs a menudo imprime progreso en stderr
                text=True,
                bufsize=1, # Line-buffered para latencia de lectura cero
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            # 3. Análisis diferencial de la salida estándar (Regex)
            # Expresión regular para capturar porcentajes tipo " 45%" o "45.5%"
            progress_pattern = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")

            for line in self._process.stdout:
                match = progress_pattern.search(line)
                if match:
                    # Extracción del escalar y normalización
                    percent_val = float(match.group(1))
                    on_progress(percent_val)

            # 4. Espera de la terminación formal del subproceso
            self._process.wait()
            return_code = self._process.returncode

            self._is_running = False

            if return_code == 0:
                on_complete(return_code)
            else:
                on_error(f"El subproceso finalizó con un estado anómalo: {return_code}")

        except Exception as e:
            self._is_running = False
            on_error(str(e))

    def terminate(self):
        """
        Interrupción forzada del grafo computacional. Envía señal SIGTERM al subproceso.
        """
        if self._process and self._is_running:
            self._process.terminate()
            self._is_running = False

# ==========================================
# Ejemplo de Evaluación Lógica del Sistema:
# ==========================================
if __name__ == "__main__":
    # Escenario 1: Usuario elige nivel PRO pero su sistema solo tiene CPU
    print("--- Prueba 1: CPU + Nivel PRO ---")
    config_cpu = DemucsInferenceConfig(
        device=ComputeDevice.CPU,
        quality=QualityLevel.PRO,
        stem=TargetStem.OTHER
    )
    print(f"Estado final asignado: {config_cpu.quality.label}")
    print(f"Argumentos generados: {config_cpu.get_demucs_args()}\n")

    # Escenario 2: Usuario con GPU (CUDA) selecciona nivel PRO
    print("--- Prueba 2: CUDA + Nivel PRO ---")
    config_cuda = DemucsInferenceConfig(
        device=ComputeDevice.CUDA,
        quality=QualityLevel.PRO,
        stem=TargetStem.OTHER
    )
    print(f"Estado final asignado: {config_cuda.quality.label}")
    print(f"Argumentos generados: {config_cuda.get_demucs_args()}")