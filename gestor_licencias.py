import subprocess
import hashlib
import platform

class CriptografiaHWID:
    def __init__(self, semilla_secreta="GuitarNotebook_DSP_Axioma"):
        """Inicializa el motor criptográfico con una semilla inmutable."""
        self.semilla_secreta = semilla_secreta

    def extraer_hardware_serial(self):
        """Extrae el número de serie físico de la placa base (macOS)."""
        if platform.system() == "Darwin": 
            try:
                comando = "system_profiler SPHardwareDataType | grep 'Serial Number'"
                salida = subprocess.check_output(comando, shell=True).decode('utf-8')
                serial_mac = salida.split(':')[1].strip()
                return serial_mac
            except Exception as e:
                raise RuntimeError(f"Fallo en lectura de matriz de silicio: {e}")
        else:
            raise NotImplementedError("Arquitectura no soportada en esta iteración.")

    def generar_llave_maestra(self, serial_fisico):
        """Genera un tensor hexadecimal de 64 caracteres vía SHA-256."""
        cadena_base = f"{serial_fisico}_{self.semilla_secreta}"
        hash_seguridad = hashlib.sha256(cadena_base.encode('utf-8')).hexdigest()
        return hash_seguridad