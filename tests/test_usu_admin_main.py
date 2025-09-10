import sys
import os
import unittest
from unittest.mock import Mock
import tkinter as tk
import ttkbootstrap as tb

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from Usuario_administrador.usu_admin_main import usuAdminMain
from Usuario_administrador.validacion_dialog import lanzar_validacion

def generar_archivo_mock():
    return {
        "nombre_archivo": "arch1.mdb",
        "ruta": "/tmp/arch1.mdb",
        "path": "/tmp/arch1.mdb",
        "rel_path": "arch1.mdb",
        "fecha_mod": 1700000000,
        "tipo": "sp",
    }

class DummyPanel:
    def __init__(self, ambientes, seleccionados_idx):
        self.ambientes = ambientes
        self.ambientes_vars = [Mock(get=Mock(return_value=(i in seleccionados_idx))) for i in range(len(ambientes))]
    def get_seleccionados(self):
        return [i for i, v in enumerate(self.ambientes_vars) if v.get()]

class TestUsuAdminMain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.style = tb.Style()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_integra_con_lanzar_validacion(self):
        # Puedes simular los datos igual que el flujo natural de la app
        archivos_unicos = [generar_archivo_mock()]
        seleccionados_idx = [0]
        ambientes_panel = DummyPanel([
            {"nombre": "AmbienteX"}
        ], seleccionados_idx)
        
        # Aquí asegúrate de que no explota el flujo normal
        lanzar_validacion(self.root, archivos_unicos, seleccionados_idx, ambientes_panel)
        # Si aquí hay un error, es un desacople real entre test y producción

    def test_integra_lanzar_validacion_con_panel_invalido(self):
        # Caso negativo: si pásas un panel sin la interfaz adecuada, debe fallar
        class BadPanel:
            def __init__(self):
                self.ambientes = [{"nombre": "Error"}]
        archivos_unicos = [generar_archivo_mock()]
        seleccionados_idx = [0]
        ambientes_panel = BadPanel()
        with self.assertRaises(Exception):
            lanzar_validacion(self.root, archivos_unicos, seleccionados_idx, ambientes_panel)

if __name__ == '__main__':
    unittest.main()