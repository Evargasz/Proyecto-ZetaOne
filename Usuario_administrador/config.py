import json
import os
from typing import List, Dict, Any
import logging
import shutil
import base64  # <-- Se añade la importación necesaria

import sys # <-- Se añade import faltante
# --- Import clave para que las rutas funcionen en el .exe ---
from util_rutas import recurso_path

# Tu función para manejar archivos corruptos se mantiene intacta
def cargar_seguro_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        corrupted_path = f"{path}.corrupto"
        shutil.move(path, corrupted_path)
        print(f"Archivo corrupto movido (respaldado): {corrupted_path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default if default is not None else [], f, indent=2, ensure_ascii=False)
        return default if default is not None else []
    except FileNotFoundError:
        return default if default is not None else []

# --- SOLUCIÓN: La función 'cargar_ambientes' ahora lee y decodifica 'ambientes.dat' ---
def cargar_ambientes() -> List[Dict[str, Any]]:
    """
    Carga la lista de ambientes desde el archivo .dat ofuscado.
    """
    # 1. Apunta al archivo ofuscado usando una ruta segura
    ruta_config_dat = recurso_path("json", "ambientes.dat")
    
    try:
        # 2. Lee el archivo en modo binario
        with open(ruta_config_dat, 'rb') as f:
            contenido_codificado = f.read()
        
        # 3. Decodifica el contenido desde Base64
        contenido_bytes = base64.b64decode(contenido_codificado)
        contenido_json_str = contenido_bytes.decode('utf-8')
        
        # 4. Convierte el texto JSON a una lista de Python
        ambientes = json.loads(contenido_json_str)
        
        if isinstance(ambientes, list):
            return ambientes
        logging.error("El archivo de configuración decodificado no tiene formato de lista.")
        return []
    except FileNotFoundError:
        logging.error(f"Error crítico: No se encontró el archivo de configuración 'ambientes.dat'.")
        # Aquí podrías usar messagebox si la librería estuviera disponible
        return []
    except Exception as e:
        logging.error(f"Error al cargar o decodificar la configuración de ambientes: {e}")
        return []

# Tu función para guardar se mantiene, aunque ahora la carga es desde el .dat
def guardar_ambientes(ambientes: List[Dict[str, Any]]) -> None:
    """
    Guarda la lista de ambientes en el archivo .dat ofuscado.
    """
    try:
        # 1. Convertir la lista de Python a una cadena de texto JSON
        contenido_json_str = json.dumps(ambientes, indent=2, ensure_ascii=False)
        contenido_bytes = contenido_json_str.encode('utf-8')
        
        # 2. Codificar el contenido a Base64
        contenido_codificado = base64.b64encode(contenido_bytes)

        # 3. Determinar la ruta de guardado correcta (funciona en desarrollo y en el .exe)
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(".")
        
        ruta_guardado = os.path.join(base_path, "json", "ambientes.dat")
        os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)

        # 4. Escribir el contenido codificado en el archivo .dat
        with open(ruta_guardado, 'wb') as f:
            f.write(contenido_codificado)

    except Exception as e:
        logging.error(f"Error al guardar ambientes: {e}")