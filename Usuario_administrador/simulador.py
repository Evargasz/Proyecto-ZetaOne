# core/simulador.py
import os
import sys
import subprocess
import webbrowser

def obtener_ruta_recurso(*partes_ruta):
    """Obtiene la ruta correcta a un recurso, funcionando en dev y en .exe."""
    try:
        # PyInstaller crea una carpeta temporal y la guarda en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, *partes_ruta)

def cargar_accesos():
    """Lee y procesa el archivo Accesos.txt desde la raíz del proyecto."""
    accesos = []
    # El archivo está en la raíz, no en una subcarpeta 'data'
    ruta_archivo = obtener_ruta_recurso("Accesos.txt")
    
    if not os.path.exists(ruta_archivo):
        print(f"ADVERTENCIA: No se encontró el archivo en {ruta_archivo}")
        return []

    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        for linea in f:
            # Ignorar líneas vacías o comentarios
            if linea.strip() and not linea.strip().startswith('#'):
                try:
                    tipo, usuario, clave, ruta = linea.strip().split(',', 3)
                    accesos.append({
                        "tipo": tipo.strip(),
                        "usuario": usuario.strip(),
                        "clave": clave.strip(),
                        "ruta": ruta.strip()
                    })
                except ValueError:
                    print(f"ADVERTENCIA: Omitiendo línea mal formada: {linea.strip()}")
    return accesos

def simular_acceso(acceso):
    """
    Simula el acceso según el tipo.
    Devuelve (True, "Mensaje de éxito") o (False, "Mensaje de error").
    """
    print(f"Simulando acceso para '{acceso['usuario']}' a '{acceso['ruta']}'...")

    if acceso['tipo'] == 'exe':
        if not os.path.exists(acceso['ruta']):
            return False, f"Error: El archivo .exe no se encontró en:\n{acceso['ruta']}"
        try:
            subprocess.Popen(acceso['ruta'])
            return True, f"Aplicación '{os.path.basename(acceso['ruta'])}' iniciada."
        except Exception as e:
            return False, f"Error al intentar ejecutar el .exe:\n{e}"

    elif acceso['tipo'] == 'url':
        try:
            webbrowser.open(acceso['ruta'])
            return True, f"URL abierta en el navegador."
        except Exception as e:
            return False, f"Error al intentar abrir la URL:\n{e}"
            
    return False, "Tipo de acceso desconocido."