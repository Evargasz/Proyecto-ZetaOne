import sys
import os
import unittest
from unittest.mock import Mock
import tkinter as tk
import ttkbootstrap as tb

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

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
        # Replicamos la estructura de ambientes_vars de AmbientesPanel real:
        self.ambientes_vars = [Mock(get=Mock(return_value=(i in seleccionados_idx))) for i in range(len(ambientes))]
    def get_seleccionados(self):
        return [i for i, v in enumerate(self.ambientes_vars) if v.get()]

class TestValidacionDialogIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.style = tb.Style()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_lanzar_validacion_invo_caso_ok(self):
        archivos_unicos = [generar_archivo_mock()]
        seleccionados_idx = [0]
        ambientes_panel = DummyPanel([
            {"nombre": "Ambiente1"},
            {"nombre": "Ambiente2"}
        ], seleccionados_idx)

        # El flujo debe pasar SIN fallar. Si algo está mal, el error saldrá y el test marcará excepción/fallo
        lanzar_validacion(self.root, archivos_unicos, seleccionados_idx, ambientes_panel)
        # Si llegaste aquí, la validación pasó correctamente.

    def test_lanzar_validacion_error_por_panel_invalido(self):
        # Simula el error pasando un panel sin método ni atributo esperado
        class BadPanel:
            def __init__(self):
                self.ambientes = [{"nombre": "Falso"}]
        archivos_unicos = [generar_archivo_mock()]
        seleccionados_idx = [0]
        ambientes_panel = BadPanel()
        with self.assertRaises(Exception):  # Se espera excepción o error controlado
            lanzar_validacion(self.root, archivos_unicos, seleccionados_idx, ambientes_panel)

    def test_lanzar_validacion_error_por_todo_none(self):
        archivos_unicos = None
        seleccionados_idx = None
        ambientes_panel = None
        with self.assertRaises(Exception):
            lanzar_validacion(self.root, archivos_unicos, seleccionados_idx, ambientes_panel)

if __name__ == '__main__':
    unittest.main()