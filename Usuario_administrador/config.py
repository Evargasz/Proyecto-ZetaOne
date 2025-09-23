import json
import os
from typing import List, Dict, Any
import logging
import shutil
import base64  # <-- Se añade la importación necesaria

import sys # <-- Se añade import faltante
# --- Import clave para que las rutas funcionen en el .exe ---
from util_rutas import recurso_path

# --- SOLUCIÓN: Función para obtener una ruta de datos de usuario escribible ---
def obtener_ruta_appdata(*partes_ruta):
    """
    Devuelve una ruta dentro de la carpeta de datos de la aplicación del usuario.
    Ej: C:\\Users\\<usuario>\\AppData\\Local\\ZetaOne\\...
    """
    # Usamos os.path.expandvars para resolver %LOCALAPPDATA%
    base_path = os.path.join(os.path.expandvars('%LOCALAPPDATA%'), 'ZetaOne')
    # Nos aseguramos de que la carpeta base exista
    os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, *partes_ruta)

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
    Carga la lista de ambientes. Primero busca en la carpeta de datos del usuario.
    Si no existe, usa el archivo por defecto que viene con la instalación.
    """
    # 1. Prioridad 1: Intentar cargar desde la carpeta de datos del usuario.
    ruta_usuario = obtener_ruta_appdata("json", "ambientes.dat")
    
    # 2. Prioridad 2 (fallback): Usar el archivo por defecto de la instalación.
    ruta_defecto = recurso_path("json", "ambientes.dat")

    # Determinar qué ruta usar
    ruta_a_cargar = ruta_usuario if os.path.exists(ruta_usuario) else ruta_defecto
    
    try:
        # Lee el archivo en modo binario desde la ruta determinada
        with open(ruta_a_cargar, 'rb') as f:
            contenido_codificado = f.read()
        
        # Decodifica el contenido desde Base64
        contenido_bytes = base64.b64decode(contenido_codificado)
        contenido_json_str = contenido_bytes.decode('utf-8')
        
        # Convierte el texto JSON a una lista de Python
        ambientes = json.loads(contenido_json_str)
        
        if isinstance(ambientes, list):
            return ambientes
        logging.error("El archivo de configuración decodificado no tiene formato de lista.")
        return []
    except FileNotFoundError:
        logging.error(f"Error crítico: No se encontró el archivo de configuración 'ambientes.dat' en ninguna ubicación.")
        # Aquí podrías usar messagebox si la librería estuviera disponible
        return []
    except Exception as e:
        logging.error(f"Error al cargar o decodificar la configuración de ambientes: {e}")
        return []

# Tu función para guardar se mantiene, aunque ahora la carga es desde el .dat
def guardar_ambientes(ambientes: List[Dict[str, Any]]) -> None:
    """
    Guarda la lista de ambientes SIEMPRE en la carpeta de datos del usuario.
    """
    try:
        # 1. Convertir la lista de Python a una cadena de texto JSON
        contenido_json_str = json.dumps(ambientes, indent=2, ensure_ascii=False)
        contenido_bytes = contenido_json_str.encode('utf-8')
        
        # 2. Codificar el contenido a Base64
        contenido_codificado = base64.b64encode(contenido_bytes)

        # 3. Obtener la ruta de guardado en la carpeta de datos del usuario.
        ruta_guardado = obtener_ruta_appdata("json", "ambientes.dat")
        os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)

        # 4. Escribir el contenido codificado en el archivo.
        with open(ruta_guardado, 'wb') as f:
            f.write(contenido_codificado)

    except Exception as e:
        logging.error(f"Error al guardar ambientes: {e}")