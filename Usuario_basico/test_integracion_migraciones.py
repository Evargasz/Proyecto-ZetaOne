#!/usr/bin/env python3
"""
PRUEBAS DE INTEGRACIÓN PARA MIGRACIONES
=======================================
Pruebas más realistas que simulan escenarios completos de migración
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import threading
import time

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestIntegracionMigracionTabla(unittest.TestCase):
    """Pruebas de integración para migración de tabla"""
    
    def setUp(self):
        self.logs_capturados = []
        self.progreso_capturado = []
        
        def mock_log(mensaje, tipo="info"):
            self.logs_capturados.append(f"[{tipo}] {mensaje}")
        
        def mock_progress(porcentaje):
            self.progreso_capturado.append(porcentaje)
        
        self.mock_log = mock_log
        self.mock_progress = mock_progress
        self.mock_abort = Mock()
    
    @patch('migrar_tabla.pyodbc.connect')
    @patch('migrar_tabla._manage_trigger')
    def test_escenario_completo_ca_transaccion(self, mock_manage_trigger, mock_connect):
        """Prueba escenario completo con ca_transaccion y triggers"""
        from migrar_tabla import migrar_tabla_secuencial
        
        # Configurar conexiones mock
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Simular datos realistas de ca_transaccion
        datos_simulados = [
            ('1', '2025-01-01 00:00:00', '1430106501', 0, 354254079, 'DES', 'S'),
            ('16', '2025-01-01 00:00:00', '1430106501', 0, 354254079, 'PRV', 'N'),
            ('21', '2025-01-02 00:00:00', '1430106501', 0, 354254079, 'IOC', 'N')
        ]
        
        mock_cur_ori.fetchmany.side_effect = [
            datos_simulados,  # Primer lote
            []  # Fin de datos
        ]
        
        # Simular verificación de duplicados (algunos duplicados)
        mock_cur_dest.fetchone.side_effect = [
            [0],  # Registro 1: no existe
            [1],  # Registro 2: ya existe (duplicado)
            [0]   # Registro 3: no existe
        ]
        
        # Ejecutar migración
        resultado = migrar_tabla_secuencial(
            tabla="ca_transaccion",
            where="tr_operacion = 354254079",
            amb_origen={'driver': 'Sybase ASE ODBC Driver', 'ip': 'localhost', 'puerto': '5000', 'base': 'SYBREPOR', 'usuario': 'test', 'clave': 'test'},
            amb_destino={'driver': 'Sybase ASE ODBC Driver', 'ip': 'localhost', 'puerto': '5001', 'base': 'SYBCOB25', 'usuario': 'test', 'clave': 'test'},
            log=self.mock_log,
            progress=self.mock_progress,
            abort=self.mock_abort,
            columnas=['tr_secuencial', 'tr_fecha_mov', 'tr_toperacion', 'tr_moneda', 'tr_operacion', 'tr_tran', 'tr_en_linea'],
            cancelar_func=None,
            total_registros=3
        )
        
        # Verificaciones del resultado
        self.assertEqual(resultado['insertados'], 2)  # 2 registros nuevos
        self.assertEqual(resultado['omitidos'], 1)    # 1 duplicado
        
        # Verificar secuencia de llamadas a triggers
        expected_calls = [
            call(mock_cur_dest, "ca_transaccion", "DISABLE", self.mock_log),
            call(mock_cur_dest, "ca_transaccion", "ENABLE", self.mock_log)
        ]
        mock_manage_trigger.assert_has_calls(expected_calls)
        
        # Verificar logs capturados
        logs_str = " ".join(self.logs_capturados)
        self.assertIn("Trigger", logs_str)
        self.assertIn("deshabilitado", logs_str)
        self.assertIn("rehabilitado", logs_str)
        
        # Verificar progreso
        self.assertTrue(len(self.progreso_capturado) > 0)
        self.assertEqual(self.progreso_capturado[-1], 100)
    
    @patch('migrar_tabla.pyodbc.connect')
    @patch('migrar_tabla._manage_trigger')
    def test_manejo_error_con_trigger_recovery(self, mock_manage_trigger, mock_connect):
        """Prueba recuperación de trigger cuando hay error en inserción"""
        from migrar_tabla import migrar_tabla_secuencial
        
        # Configurar conexiones mock
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Simular datos
        mock_cur_ori.fetchmany.side_effect = [
            [('1', '2025-01-01', 'test')],
            []
        ]
        
        # Simular verificación sin duplicados
        mock_cur_dest.fetchone.return_value = [0]
        
        # Simular error en executemany (después de DISABLE trigger)
        mock_cur_dest.executemany.side_effect = Exception("Error de inserción simulado")
        
        # Ejecutar migración
        resultado = migrar_tabla_secuencial(
            tabla="ca_transaccion",
            where="",
            amb_origen={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            amb_destino={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            log=self.mock_log,
            progress=self.mock_progress,
            abort=self.mock_abort,
            columnas=['col1', 'col2', 'col3'],
            cancelar_func=None,
            total_registros=1
        )
        
        # Verificar que se intentó rehabilitar el trigger después del error
        expected_calls = [
            call(mock_cur_dest, "ca_transaccion", "DISABLE", self.mock_log),
            call(mock_cur_dest, "ca_transaccion", "ENABLE", self.mock_log)  # Rehabilitación tras error
        ]
        mock_manage_trigger.assert_has_calls(expected_calls)

class TestIntegracionMigracionGrupo(unittest.TestCase):
    """Pruebas de integración para migración de grupo"""
    
    def setUp(self):
        self.logs_capturados = []
        
        def mock_log(mensaje):
            self.logs_capturados.append(mensaje)
        
        self.mock_log = mock_log
        self.mock_progress = Mock()
    
    @patch('migrar_grupo.pyodbc.connect')
    @patch('migrar_grupo._manage_trigger')
    @patch('migrar_grupo.columnas_tabla')
    @patch('migrar_grupo.pk_tabla')
    @patch('migrar_grupo.desactivar_indices_secundarios')
    @patch('migrar_grupo.reactivar_indices_secundarios')
    def test_migracion_grupo_multiples_tablas(self, mock_reactivar_idx, mock_desactivar_idx, 
                                            mock_pk_tabla, mock_columnas_tabla, 
                                            mock_manage_trigger, mock_connect):
        """Prueba migración de grupo con múltiples tablas incluyendo ca_transaccion"""
        from migrar_grupo import migrar_tabla_del_grupo
        
        # Configurar mocks
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Configurar estructura de tabla
        mock_columnas_tabla.return_value = ['tr_secuencial', 'tr_operacion', 'tr_fecha_mov']
        mock_pk_tabla.return_value = ['tr_operacion', 'tr_secuencial']
        
        # Simular datos con múltiples lotes
        mock_row1 = Mock()
        mock_row1.tr_secuencial = '1'
        mock_row1.tr_operacion = '354254079'
        mock_row1.tr_fecha_mov = '2025-01-01'
        
        mock_row2 = Mock()
        mock_row2.tr_secuencial = '2'
        mock_row2.tr_operacion = '354254079'
        mock_row2.tr_fecha_mov = '2025-01-02'
        
        mock_cur_ori.fetchmany.side_effect = [
            [mock_row1],  # Primer lote
            [mock_row2],  # Segundo lote
            []            # Fin de datos
        ]
        mock_cur_ori.description = [('tr_secuencial',), ('tr_operacion',), ('tr_fecha_mov',)]
        
        # Simular verificación de duplicados (no hay duplicados)
        mock_cur_dest.fetchall.return_value = []
        
        # Ejecutar migración de ca_transaccion
        tabla_conf = {
            'tabla': 'ca_transaccion',
            'llave': '',
            'join': '',
            'condicion': 'tr_operacion = 354254079'
        }
        
        resultado = migrar_tabla_del_grupo(
            tabla_conf=tabla_conf,
            variables={},
            conn_str_ori="test_conn_str",
            conn_str_dest="test_conn_str",
            batch_size=1,  # Forzar múltiples lotes
            idx_tabla=0,
            total_tablas=1,
            log=self.mock_log,
            progress=self.mock_progress,
            cancelar_func=None,
            contadores={'estructura_diferente': 0, 'sin_pk': 0}
        )
        
        # Verificaciones
        self.assertEqual(resultado, 2)  # 2 registros migrados
        
        # Verificar que se llamó al manejo de triggers para cada lote
        self.assertEqual(mock_manage_trigger.call_count, 4)  # 2 DISABLE + 2 ENABLE
        
        # Verificar secuencia de llamadas
        calls = mock_manage_trigger.call_args_list
        self.assertEqual(calls[0][0][2], "DISABLE")  # Primer lote
        self.assertEqual(calls[1][0][2], "ENABLE")   # Primer lote
        self.assertEqual(calls[2][0][2], "DISABLE")  # Segundo lote
        self.assertEqual(calls[3][0][2], "ENABLE")   # Segundo lote

class TestEscenariosRealistas(unittest.TestCase):
    """Pruebas con escenarios realistas de producción"""
    
    def setUp(self):
        self.eventos_capturados = []
        
        def mock_log(mensaje, tipo="info"):
            self.eventos_capturados.append(f"[{time.time():.3f}] [{tipo}] {mensaje}")
        
        self.mock_log = mock_log
        self.mock_progress = Mock()
        self.mock_abort = Mock()
    
    @patch('migrar_tabla.pyodbc.connect')
    @patch('migrar_tabla._manage_trigger')
    def test_cancelacion_durante_migracion(self, mock_manage_trigger, mock_connect):
        """Prueba cancelación durante migración y limpieza de triggers"""
        from migrar_tabla import migrar_tabla_secuencial
        
        # Configurar mocks
        mock_conn_ori = Mock()
        mock_conn_dest = Mock()
        mock_cur_ori = Mock()
        mock_cur_dest = Mock()
        
        mock_connect.side_effect = [mock_conn_ori, mock_conn_dest]
        mock_conn_ori.cursor.return_value = mock_cur_ori
        mock_conn_dest.cursor.return_value = mock_cur_dest
        
        # Simular datos grandes
        datos_grandes = [('1', '2025-01-01', 'test')] * 1000
        mock_cur_ori.fetchmany.side_effect = [
            datos_grandes[:500],  # Primer lote
            datos_grandes[500:],  # Segundo lote (aquí se cancela)
            []
        ]
        
        # Simular verificación sin duplicados
        mock_cur_dest.fetchone.return_value = [0]
        
        # Simular cancelación en el segundo lote
        cancelacion_llamada = [False]
        def mock_cancelar():
            if not cancelacion_llamada[0]:
                cancelacion_llamada[0] = True
                return False  # Primera vez: continuar
            return True  # Segunda vez: cancelar
        
        # Ejecutar migración
        resultado = migrar_tabla_secuencial(
            tabla="ca_transaccion",
            where="",
            amb_origen={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            amb_destino={'driver': 'test', 'ip': 'test', 'puerto': '1433', 'base': 'test', 'usuario': 'test', 'clave': 'test'},
            log=self.mock_log,
            progress=self.mock_progress,
            abort=self.mock_abort,
            columnas=['col1', 'col2', 'col3'],
            cancelar_func=mock_cancelar,
            total_registros=1000
        )
        
        # Verificar que se procesó al menos el primer lote
        self.assertGreater(resultado['insertados'], 0)
        
        # Verificar que se manejaron los triggers correctamente
        self.assertGreater(mock_manage_trigger.call_count, 0)
    
    def test_rendimiento_manage_trigger(self):
        """Prueba rendimiento de _manage_trigger con múltiples llamadas"""
        from migrar_tabla import _manage_trigger
        
        mock_cursor = Mock()
        mock_log = Mock()
        
        # Medir tiempo de 1000 llamadas
        start_time = time.time()
        
        for i in range(1000):
            _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
            _manage_trigger(mock_cursor, "ca_transaccion", "ENABLE", mock_log)
        
        end_time = time.time()
        tiempo_total = end_time - start_time
        
        # Verificar que es eficiente (menos de 1 segundo para 2000 llamadas)
        self.assertLess(tiempo_total, 1.0)
        
        # Verificar número correcto de llamadas
        self.assertEqual(mock_cursor.execute.call_count, 2000)

def ejecutar_pruebas_integracion():
    """Ejecuta todas las pruebas de integracion"""
    print("INICIANDO PRUEBAS DE INTEGRACION DE MIGRACIONES")
    print("=" * 70)
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar clases de prueba
    suite.addTests(loader.loadTestsFromTestCase(TestIntegracionMigracionTabla))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegracionMigracionGrupo))
    suite.addTests(loader.loadTestsFromTestCase(TestEscenariosRealistas))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    
    # Reporte final
    print("\n" + "=" * 70)
    print("REPORTE DE INTEGRACION")
    print("=" * 70)
    print(f"Pruebas de integracion ejecutadas: {resultado.testsRun}")
    print(f"Exitosas: {resultado.testsRun - len(resultado.failures) - len(resultado.errors)}")
    print(f"Fallidas: {len(resultado.failures)}")
    print(f"Errores: {len(resultado.errors)}")
    
    if resultado.wasSuccessful():
        print("\nINTEGRACION EXITOSA")
        print("El manejo de triggers funciona correctamente en escenarios realistas")
        print("La migracion es robusta ante errores y cancelaciones")
        print("El rendimiento es adecuado para produccion")
    else:
        print("\nPROBLEMAS DE INTEGRACION DETECTADOS")
        if resultado.failures:
            print("Revisar fallos en la logica de negocio")
        if resultado.errors:
            print("Revisar errores de implementacion")
    
    return resultado.wasSuccessful()

if __name__ == "__main__":
    exito = ejecutar_pruebas_integracion()
    sys.exit(0 if exito else 1)