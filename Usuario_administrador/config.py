import json
import os
from typing import List, Dict, Any
import logging
import shutil

def cargar_seguro_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        corrupted_path = f"{path}.corrupto"
        shutil.move(path, corrupted_path)
        print(f"Archivo corrupto movido (respaldado): {corrupted_path}")
        # Si tienes acceso a messagebox aquí, puedes notificarlo al usuario
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default if default is not None else [], f, indent=2, ensure_ascii=False)
        return default if default is not None else []
    except FileNotFoundError:
        return default if default is not None else []
    
AMBIENTES_CONFIG = "json/ambientes.json"

def cargar_ambientes() -> List[Dict[str, Any]]:
    """
    Carga la lista de ambientes desde un archivo JSON.

    Returns:
        List[Dict]: Lista de ambientes o lista vacía si hay error.
    """
    if os.path.exists(AMBIENTES_CONFIG):
        try:
            with open(AMBIENTES_CONFIG, "r", encoding="utf-8") as f:
                ambientes = json.load(f)
                if isinstance(ambientes, list):
                    return ambientes
                logging.error("El archivo de ambientes no tiene formato de lista.")
        except Exception as e:
            logging.error(f"Error al cargar ambientes: {e}")
    return []

def guardar_ambientes(ambientes: List[Dict[str, Any]]) -> None:
    """
    Guarda la lista de ambientes en un archivo JSON.

    Args:
        ambientes (List[Dict]): Ambientes a guardar.
    """
    try:
        with open(AMBIENTES_CONFIG, "w", encoding="utf-8") as f:
            json.dump(ambientes, f, indent=2)
    except Exception as e:
        logging.error(f"Error al guardar ambientes: {e}")