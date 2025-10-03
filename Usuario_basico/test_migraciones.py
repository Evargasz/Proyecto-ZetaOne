#!/usr/bin/env python3
"""
PRUEBAS DE FLUJO PARA MIGRACIONES
=================================
Pruebas exhaustivas para migrar_tabla.py y migrar_grupo.py
Simula diferentes escenarios sin necesidad de bases de datos reales
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar los módulos a probar
try:
    from migrar_tabla import _manage_trigger, migrar_tabla_secuencial, migrar_tabla
    from migrar_grupo import _manage_trigger as _manage_trigger_grupo, migrar_tabla_del_grupo
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrese de que los archivos migrar_tabla.py y migrar_grupo.py estén en el directorio actual")
    sys.exit(1)

class TestManageTrigger(unittest.TestCase):
    """Pruebas para la función _manage_trigger"""
    
    def setUp(self):
        self.mock_cursor = Mock()
        self.mock_log = Mock()
    
    def test_manage_trigger_ca_transaccion_disable(self):
        """Prueba deshabilitar trigger en ca_transaccion"""
        _manage_trigger(self.mock_cursor, "ca_transaccion", "DISABLE", self.mock_log)
        
        self.mock_cursor.execute.assert_called_once_with(
            "ALTER TABLE ca_transaccion DISABLE TRIGGER tg_ca_transaccion"
        )
        self.mock_log.assert_called_once()
        self.assertIn("deshabilitado", self.mock_log.call_args[0][0])
    
    def test_manage_trigger_ca_transaccion_enable(self):
        """Prueba habilitar trigger en ca_transaccion"""
        _manage_trigger(self.mock_cursor, "ca_transaccion", "ENABLE", self.mock_log)
        
        self.mock_cursor.execute.assert_called_once_with(
            "ALTER TABLE ca_transaccion ENABLE TRIGGER tg_ca_transaccion"
        )
        self.mock_log.assert_called_once()
        self.assertIn("rehabilitado", self.mock_log.call_args[0][0])
    
    def test_manage_trigger_otra_tabla(self):
        """Prueba que no afecte otras tablas"""
        _manage_trigger(self.mock_cursor, "otra_tabla", "DISABLE", self.mock_log)
        
        self.mock_cursor.execute.assert_not_called()
        self.mock_log.assert_not_called()
    
    def test_manage_trigger_error_sql(self):
        """Prueba manejo de errores SQL"""
        self.mock_cursor.execute.side_effect = Exception("SQL Error")
        
        _manage_trigger(self.mock_cursor, "ca_transaccion", "DISABLE", self.mock_log)
        
        self.mock_log.assert_called_once()
        self.assertIn("Error", self.mock_log.call_args[0][0])

class TestMigracionTablaSecuencial(unittest.TestCase):
    """Pruebas para migración secuencial de tabla"""
    
    def setUp(self):
        self.mock_log = Mock()
        self.mock_progress = Mock()
        self.mock_abort = Mock()
        
    @patch('migrar_tabla.pyodbc.connect')
    @patch('migrar_tabla._manage_trigger')
    def test_migracion_exitosa_pequena(self, mock_manage_trigger, mock_connect):
        """Prueba migración exitosa de dataset pequeño"""
        # Configurar mocks
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Simular datos de origen
        mock_cur_ori.fetchmany.side_effect = [
            [('1', '2025-01-01', 'test')],  # Primer lote
            []  # Fin de datos
        ]
        
        # Simular verificación de duplicados (no hay duplicados)
        mock_cur_dest.fetchone.return_value = [0]
        
        # Ejecutar migración
        resultado = migrar_tabla_secuencial(
            tabla="ca_transaccion",
            where="",
            amb_origen={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            amb_destino={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            log=self.mock_log,
            progress=self.mock_progress,
            abort=self.mock_abort,
            columnas=['tr_secuencial', 'tr_fecha_mov', 'tr_toperacion'],
            cancelar_func=None,
            total_registros=1
        )
        
        # Verificaciones
        self.assertEqual(resultado['insertados'], 1)
        self.assertEqual(resultado['omitidos'], 0)
        
        # Verificar que se llamó al manejo de triggers
        mock_manage_trigger.assert_any_call(mock_cur_dest, "ca_transaccion", "DISABLE", self.mock_log)
        mock_manage_trigger.assert_any_call(mock_cur_dest, "ca_transaccion", "ENABLE", self.mock_log)
    
    @patch('migrar_tabla.pyodbc.connect')
    @patch('migrar_tabla._manage_trigger')
    def test_migracion_con_duplicados(self, mock_manage_trigger, mock_connect):
        """Prueba migración con registros duplicados"""
        # Configurar mocks
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Simular datos de origen
        mock_cur_ori.fetchmany.side_effect = [
            [('1', '2025-01-01', 'test')],  # Primer lote
            []  # Fin de datos
        ]
        
        # Simular verificación de duplicados (hay duplicados)
        mock_cur_dest.fetchone.return_value = [1]  # Ya existe
        
        # Ejecutar migración
        resultado = migrar_tabla_secuencial(
            tabla="ca_transaccion",
            where="",
            amb_origen={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            amb_destino={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            log=self.mock_log,
            progress=self.mock_progress,
            abort=self.mock_abort,
            columnas=['tr_secuencial', 'tr_fecha_mov', 'tr_toperacion'],
            cancelar_func=None,
            total_registros=1
        )
        
        # Verificaciones
        self.assertEqual(resultado['insertados'], 0)
        self.assertEqual(resultado['omitidos'], 1)

class TestMigracionGrupo(unittest.TestCase):
    """Pruebas para migración de grupo"""
    
    def setUp(self):
        self.mock_log = Mock()
        self.mock_progress = Mock()
    
    @patch('migrar_grupo.pyodbc.connect')
    @patch('migrar_grupo._manage_trigger')
    @patch('migrar_grupo.columnas_tabla')
    @patch('migrar_grupo.pk_tabla')
    def test_migracion_grupo_exitosa(self, mock_pk_tabla, mock_columnas_tabla, mock_manage_trigger, mock_connect):
        """Prueba migración exitosa de grupo"""
        # Configurar mocks
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Configurar estructura de tabla
        mock_columnas_tabla.return_value = ['col1', 'col2', 'col3']
        mock_pk_tabla.return_value = ['col1']
        
        # Simular datos de origen
        mock_row = Mock()
        mock_row.col1 = '1'
        mock_row.col2 = 'test'
        mock_row.col3 = '2025-01-01'
        
        mock_cur_ori.fetchmany.side_effect = [
            [mock_row],  # Primer lote
            []  # Fin de datos
        ]
        mock_cur_ori.description = [('col1',), ('col2',), ('col3',)]
        
        # Simular verificación de duplicados (no hay duplicados)
        mock_cur_dest.fetchall.return_value = []
        
        # Ejecutar migración
        tabla_conf = {
            'tabla': 'ca_transaccion',
            'llave': '',
            'join': '',
            'condicion': ''
        }
        
        resultado = migrar_tabla_del_grupo(
            tabla_conf=tabla_conf,
            variables={},
            conn_str_ori="test_conn_str",
            conn_str_dest="test_conn_str",
            batch_size=1000,
            idx_tabla=0,
            total_tablas=1,
            log=self.mock_log,
            progress=self.mock_progress,
            cancelar_func=None,
            contadores=None
        )
        
        # Verificaciones
        self.assertEqual(resultado, 1)
        
        # Verificar que se llamó al manejo de triggers
        mock_manage_trigger.assert_any_call(mock_cur_dest, 'ca_transaccion', "DISABLE", self.mock_log)
        mock_manage_trigger.assert_any_call(mock_cur_dest, 'ca_transaccion', "ENABLE", self.mock_log)

class TestFlujosCompletos(unittest.TestCase):
    """Pruebas de flujos completos end-to-end"""
    
    def setUp(self):
        self.mock_log = Mock()
        self.mock_progress = Mock()
        self.mock_abort = Mock()
    
    @patch('migrar_tabla.migrar_tabla_secuencial')
    def test_flujo_dataset_pequeno(self, mock_migrar_secuencial):
        """Prueba flujo completo para dataset pequeño"""
        mock_migrar_secuencial.return_value = {'insertados': 5, 'omitidos': 1}
        
        resultado = migrar_tabla(
            tabla="ca_transaccion",
            where="",
            amb_origen={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            amb_destino={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            log_func=self.mock_log,
            progress_func=self.mock_progress,
            abort_func=self.mock_abort,
            columnas=['col1', 'col2'],
            clave_primaria=['col1'],
            total_registros=6  # Dataset pequeño
        )
        
        # Verificar que se usó migración secuencial
        mock_migrar_secuencial.assert_called_once()
        self.assertEqual(resultado['insertados'], 5)
        self.assertEqual(resultado['omitidos'], 1)

class TestEscenariosCriticos(unittest.TestCase):
    """Pruebas para escenarios críticos y edge cases"""
    
    def setUp(self):
        self.mock_log = Mock()
        self.mock_progress = Mock()
        self.mock_abort = Mock()
    
    def test_manage_trigger_sin_log(self):
        """Prueba _manage_trigger sin función de log"""
        mock_cursor = Mock()
        
        # No debería fallar sin log_func
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", None)
        
        mock_cursor.execute.assert_called_once()
    
    def test_manage_trigger_tabla_none(self):
        """Prueba _manage_trigger con tabla None"""
        mock_cursor = Mock()
        mock_log = Mock()
        
        _manage_trigger(mock_cursor, None, "DISABLE", mock_log)
        
        # No debería ejecutar nada
        mock_cursor.execute.assert_not_called()
        mock_log.assert_not_called()
    
    def test_manage_trigger_tabla_vacia(self):
        """Prueba _manage_trigger con tabla vacía"""
        mock_cursor = Mock()
        mock_log = Mock()
        
        _manage_trigger(mock_cursor, "", "DISABLE", mock_log)
        
        # No debería ejecutar nada
        mock_cursor.execute.assert_not_called()
        mock_log.assert_not_called()

def ejecutar_pruebas_completas():
    """Ejecuta todas las pruebas y genera reporte"""
    print("INICIANDO PRUEBAS DE FLUJO DE MIGRACIONES")
    print("=" * 60)
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todas las clases de prueba
    suite.addTests(loader.loadTestsFromTestCase(TestManageTrigger))
    suite.addTests(loader.loadTestsFromTestCase(TestMigracionTablaSecuencial))
    suite.addTests(loader.loadTestsFromTestCase(TestMigracionGrupo))
    suite.addTests(loader.loadTestsFromTestCase(TestFlujosCompletos))
    suite.addTests(loader.loadTestsFromTestCase(TestEscenariosCriticos))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    
    # Generar reporte final
    print("\n" + "=" * 60)
    print("REPORTE FINAL DE PRUEBAS")
    print("=" * 60)
    print(f"Pruebas ejecutadas: {resultado.testsRun}")
    print(f"Fallos: {len(resultado.failures)}")
    print(f"Errores: {len(resultado.errors)}")
    
    if resultado.failures:
        print("\nFALLOS DETECTADOS:")
        for test, traceback in resultado.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if resultado.errors:
        print("\nERRORES DETECTADOS:")
        for test, traceback in resultado.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if resultado.wasSuccessful():
        print("\nTODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("Los cambios de trigger management son SEGUROS para produccion")
    else:
        print("\nALGUNAS PRUEBAS FALLARON")
        print("Revisar los cambios antes de desplegar a produccion")
    
    return resultado.wasSuccessful()

if __name__ == "__main__":
    # Ejecutar pruebas si se ejecuta directamente
    exito = ejecutar_pruebas_completas()
    sys.exit(0 if exito else 1)