#!/usr/bin/env python3
"""
Test independiente para validar funcionalidad de triggers
Sin dependencias externas - Solo funciones críticas
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Mock del módulo styles para evitar errores de importación
sys.modules['styles'] = Mock()

# Importar las funciones de migración
try:
    from migrar_tabla import _manage_trigger as manage_trigger_tabla
    from migrar_grupo import _manage_trigger as manage_trigger_grupo
    print("✅ Módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando: {e}")
    sys.exit(1)

class TestTriggerManagement(unittest.TestCase):
    """Tests para validar manejo de triggers"""
    
    def setUp(self):
        """Configurar mocks para cada test"""
        self.mock_cursor = Mock()
        self.mock_log = Mock()
    
    def test_disable_trigger_ca_transaccion(self):
        """Test: Deshabilitar trigger en ca_transaccion"""
        manage_trigger_tabla(self.mock_cursor, "ca_transaccion", "DISABLE", self.mock_log)
        
        # Verificar que se ejecutó el SQL correcto
        self.mock_cursor.execute.assert_called_once_with(
            "ALTER TABLE ca_transaccion DISABLE TRIGGER tg_ca_transaccion"
        )
        
        # Verificar log
        self.mock_log.assert_called_with(
            "🔧 Trigger tg_ca_transaccion DESHABILITADO en ca_transaccion", "info"
        )
    
    def test_enable_trigger_ca_transaccion(self):
        """Test: Habilitar trigger en ca_transaccion"""
        manage_trigger_tabla(self.mock_cursor, "ca_transaccion", "ENABLE", self.mock_log)
        
        # Verificar SQL
        self.mock_cursor.execute.assert_called_once_with(
            "ALTER TABLE ca_transaccion ENABLE TRIGGER tg_ca_transaccion"
        )
        
        # Verificar log
        self.mock_log.assert_called_with(
            "✅ Trigger tg_ca_transaccion HABILITADO en ca_transaccion", "info"
        )
    
    def test_ignore_other_tables(self):
        """Test: Ignorar otras tablas que no sean ca_transaccion"""
        manage_trigger_tabla(self.mock_cursor, "otra_tabla", "DISABLE", self.mock_log)
        
        # No debe ejecutar SQL
        self.mock_cursor.execute.assert_not_called()
        
        # Debe logear que se ignora
        self.mock_log.assert_called_with(
            "ℹ️ Tabla otra_tabla: triggers no gestionados por esta función", "info"
        )
    
    def test_compatibility_between_modules(self):
        """Test: Verificar compatibilidad entre migrar_tabla y migrar_grupo"""
        # Ambas funciones deben comportarse igual
        manage_trigger_tabla(self.mock_cursor, "ca_transaccion", "DISABLE", self.mock_log)
        expected_call_tabla = self.mock_cursor.execute.call_args
        
        # Reset mock
        self.mock_cursor.reset_mock()
        self.mock_log.reset_mock()
        
        manage_trigger_grupo(self.mock_cursor, "ca_transaccion", "DISABLE", self.mock_log)
        expected_call_grupo = self.mock_cursor.execute.call_args
        
        # Deben ser idénticas
        self.assertEqual(expected_call_tabla, expected_call_grupo)
    
    def test_error_handling(self):
        """Test: Manejo de errores en ejecución SQL"""
        # Simular error en execute
        self.mock_cursor.execute.side_effect = Exception("SQL Error")
        
        # No debe fallar, solo logear error
        try:
            manage_trigger_tabla(self.mock_cursor, "ca_transaccion", "DISABLE", self.mock_log)
        except Exception:
            self.fail("La función no debe propagar excepciones")
        
        # Verificar que se logeó el error
        self.assertTrue(any("Error" in str(call) for call in self.mock_log.call_args_list))

def run_tests():
    """Ejecutar todos los tests"""
    print("🧪 INICIANDO TESTS DE TRIGGERS")
    print("=" * 50)
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTriggerManagement)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ TODOS LOS TESTS PASARON")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)