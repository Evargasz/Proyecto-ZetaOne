import json
import os
from typing import List, Dict, Any
import logging

AMBIENTES_CONFIG = "ambientes.json"

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