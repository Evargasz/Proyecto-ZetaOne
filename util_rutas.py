import sys
import os

def recurso_path(*rutas):
    """
    Devuelve la ruta absoluta correcta a un recurso, compatible
    tanto con PyInstaller (onefile) como con ejecución en desarrollo.
    Uso: recurso_path('imagenes_iconos', 'Zeta99.ico')
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, *rutas)