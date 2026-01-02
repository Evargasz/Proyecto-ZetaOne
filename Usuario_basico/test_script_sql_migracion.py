import unittest
from unittest.mock import Mock, patch

# Importar la clase/Método a testear
from Usuario_basico import Migracion

class FakeEntry:
    def __init__(self):
        self.value = ""
    def delete(self, a, b=None):
        self.value = ""
    def insert(self, idx, val):
        self.value = val
    def get(self):
        return self.value
    def config(self, **kwargs):
        pass

class FakeButton:
    def config(self, **kwargs):
        pass

class FakeProgress:
    def start(self, *a, **k):
        pass
    def stop(self):
        pass
    def lift(self):
        pass
    def lower(self):
        pass

class FakeSqlText:
    def config(self, **kwargs):
        pass

class FakeDialog:
    def __init__(self):
        self.progress = FakeProgress()
        self.btn_cancelar = FakeButton()
        self.btn_ejecutar = FakeButton()
        self.sql_text = FakeSqlText()

class FakeParent:
    def __init__(self):
        self.entry_db_origen = FakeEntry()
        self.entry_tabla_origen = FakeEntry()
        self.entry_where = FakeEntry()
        self.consult_called = False
    def on_consultar_tabla(self):
        self.consult_called = True

class TestMigracionScriptSQL(unittest.TestCase):
    def setUp(self):
        self.parent = FakeParent()
        # use the unbound method from Migracion.MigracionVentana
        self.method = Migracion.MigracionVentana._ejecutar_desde_script_tabla

    def test_valid_table_with_schema_and_condition(self):
        parsed = {'table': 'cob_conta_super.dbo.sb_balance', 'condition': "ba_empresa = 1 AND ba_periodo = 2024"}
        dialog = FakeDialog()
        # Call method with fake parent
        self.method(self.parent, parsed, dialog)
        self.assertEqual(self.parent.entry_db_origen.get(), 'cob_conta_super')
        self.assertEqual(self.parent.entry_tabla_origen.get(), 'sb_balance')
        self.assertEqual(self.parent.entry_where.get(), "ba_empresa = 1 AND ba_periodo = 2024")
        # Should have called consulta
        self.assertTrue(self.parent.consult_called)

    def test_valid_table_without_schema(self):
        parsed = {'table': 'mi_base.mi_tabla', 'condition': None}
        dialog = FakeDialog()
        self.method(self.parent, parsed, dialog)
        self.assertEqual(self.parent.entry_db_origen.get(), 'mi_base')
        self.assertEqual(self.parent.entry_tabla_origen.get(), 'mi_tabla')
        self.assertEqual(self.parent.entry_where.get(), '')
        self.assertTrue(self.parent.consult_called)

    def test_invalid_table_format_shows_error(self):
        parsed = {'table': 'justtable', 'condition': 'id=1'}
        dialog = FakeDialog()
        with patch('tkinter.messagebox.showerror') as mock_err:
            self.method(self.parent, parsed, dialog)
            mock_err.assert_called()

if __name__ == '__main__':
    unittest.main()
