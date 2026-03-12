from gestor_licencias import CriptografiaHWID

def fabricar_llave_maestra():
    motor = CriptografiaHWID()
    try:
        serial = motor.extraer_hardware_serial()
        llave = motor.generar_llave_maestra(serial)
        
        with open("licencia.key", "w") as f:
            f.write(llave)
            
        print(f"ÉXITO: Archivo 'licencia.key' generado para el hardware [{serial}].")
    except Exception as e:
        print(f"Error topológico: {e}")

if __name__ == "__main__":
    fabricar_llave_maestra()