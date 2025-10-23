import json
import os
import pyodbc
from cryptography.fernet import Fernet
from util_rutas import recurso_path

# --- CORRECCIÓN: Las importaciones originales eran incorrectas y causaban un error.
# Se reemplazan por las funciones que realmente se usan en este módulo.
from ..config import cargar_ambientes, guardar_ambientes
from ..sybase_utils import probar_conexion_amb

def cargar_relaciones_hijos():
    """
    Carga las relaciones entre ambientes (macroambiente -> ambientes hijos)
    desde el archivo 'ambientesrelacionados.json'.
    """
    ruta_relaciones = recurso_path("json", "ambientesrelacionados.json")
    if os.path.exists(ruta_relaciones):
        with open(ruta_relaciones, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}