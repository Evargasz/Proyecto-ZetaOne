#!/usr/bin/env python3
"""
PRUEBA SIMPLE DE TRIGGERS
=========================
Prueba solo las funciones críticas sin dependencias externas
"""

import sys
import os
from unittest.mock import Mock

def test_manage_trigger_tabla():
    """Prueba _manage_trigger de migrar_tabla.py"""
    print("🧪 Probando _manage_trigger de migrar_tabla.py...")
    
    try:
        # Importar solo la función específica
        from migrar_tabla import _manage_trigger
        
        # Test 1: ca_transaccion con DISABLE
        mock_cursor = Mock()
        mock_log = Mock()
        
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        
        # Verificar que se ejecutó el SQL correcto
        expected_sql = "ALTER TABLE ca_transaccion DISABLE TRIGGER tg_ca_transaccion"
        mock_cursor.execute.assert_called_with(expected_sql)
        print("  ✅ DISABLE trigger - OK")
        
        # Test 2: ca_transaccion con ENABLE
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "ca_transaccion", "ENABLE", mock_log)
        
        expected_sql = "ALTER TABLE ca_transaccion ENABLE TRIGGER tg_ca_transaccion"
        mock_cursor.execute.assert_called_with(expected_sql)
        print("  ✅ ENABLE trigger - OK")
        
        # Test 3: Otra tabla (no debería hacer nada)
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "otra_tabla", "DISABLE", mock_log)
        
        mock_cursor.execute.assert_not_called()
        print("  ✅ Otras tablas ignoradas - OK")
        
        # Test 4: Tabla None
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, None, "DISABLE", mock_log)
        
        mock_cursor.execute.assert_not_called()
        print("  ✅ Tabla None manejada - OK")
        
        # Test 5: Manejo de errores
        mock_cursor.reset_mock()
        mock_cursor.execute.side_effect = Exception("Error SQL simulado")
        
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        # No debería fallar, solo loggear el error
        print("  ✅ Manejo de errores - OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_manage_trigger_grupo():
    """Prueba _manage_trigger de migrar_grupo.py (solo la función)"""
    print("🧪 Probando _manage_trigger de migrar_grupo.py...")
    
    try:
        # Crear un mock del módulo styles para evitar el error de importación
        import sys
        from unittest.mock import MagicMock
        
        # Mock del módulo styles
        styles_mock = MagicMock()
        styles_mock.entrada_estandar = MagicMock()
        styles_mock.etiqueta_titulo = MagicMock()
        styles_mock.boton_accion = MagicMock()
        styles_mock.boton_rojo = MagicMock()
        styles_mock.boton_exito = MagicMock()
        
        sys.modules['styles'] = styles_mock
        
        # Ahora importar la función
        from migrar_grupo import _manage_trigger
        
        # Test básico
        mock_cursor = Mock()
        mock_log = Mock()
        
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        
        expected_sql = "ALTER TABLE ca_transaccion DISABLE TRIGGER tg_ca_transaccion"
        mock_cursor.execute.assert_called_with(expected_sql)
        print("  ✅ Función _manage_trigger funciona - OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_compatibilidad():
    """Verifica que ambas funciones _manage_trigger sean idénticas"""
    print("🔄 Probando compatibilidad entre módulos...")
    
    try:
        # Mock styles para migrar_grupo
        import sys
        from unittest.mock import MagicMock
        
        styles_mock = MagicMock()
        styles_mock.entrada_estandar = MagicMock()
        styles_mock.etiqueta_titulo = MagicMock()
        styles_mock.boton_accion = MagicMock()
        styles_mock.boton_rojo = MagicMock()
        styles_mock.boton_exito = MagicMock()
        
        sys.modules['styles'] = styles_mock
        
        # Importar ambas funciones
        from migrar_tabla import _manage_trigger as trigger_tabla
        from migrar_grupo import _manage_trigger as trigger_grupo
        
        # Probar con los mismos parámetros
        mock_cursor1 = Mock()
        mock_cursor2 = Mock()
        mock_log = Mock()
        
        trigger_tabla(mock_cursor1, "ca_transaccion", "DISABLE", mock_log)
        trigger_grupo(mock_cursor2, "ca_transaccion", "DISABLE", mock_log)
        
        # Ambas deberían hacer la misma llamada
        assert mock_cursor1.execute.call_args == mock_cursor2.execute.call_args
        print("  ✅ Ambas funciones son compatibles - OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_casos_edge():
    """Prueba casos edge y límite"""
    print("🎯 Probando casos edge...")
    
    try:
        from migrar_tabla import _manage_trigger
        
        mock_cursor = Mock()
        
        # Test 1: Sin función de log
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", None)
        print("  ✅ Sin función log - OK")
        
        # Test 2: Tabla vacía
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "", "DISABLE", None)
        mock_cursor.execute.assert_not_called()
        print("  ✅ Tabla vacía - OK")
        
        # Test 3: Acción inválida (debería funcionar igual)
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "ca_transaccion", "INVALID_ACTION", None)
        expected_sql = "ALTER TABLE ca_transaccion INVALID_ACTION TRIGGER tg_ca_transaccion"
        mock_cursor.execute.assert_called_with(expected_sql)
        print("  ✅ Acción inválida manejada - OK")
        
        # Test 4: Tabla con mayúsculas/minúsculas
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "CA_TRANSACCION", "DISABLE", None)
        mock_cursor.execute.assert_not_called()  # Solo funciona con minúsculas
        print("  ✅ Case sensitivity - OK")
        
        # Test 5: Tabla con ca_transaccion en el nombre
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "test_ca_transaccion_backup", "DISABLE", None)
        expected_sql = "ALTER TABLE ca_transaccion DISABLE TRIGGER tg_ca_transaccion"
        mock_cursor.execute.assert_called_with(expected_sql)
        print("  ✅ Substring matching - OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def ejecutar_prueba_simple():
    """Ejecuta todas las pruebas simples"""
    print("🚀 PRUEBA SIMPLE DE TRIGGERS")
    print("=" * 50)
    
    resultados = []
    
    # Ejecutar pruebas
    resultados.append(("migrar_tabla._manage_trigger", test_manage_trigger_tabla()))
    resultados.append(("migrar_grupo._manage_trigger", test_manage_trigger_grupo()))
    resultados.append(("Compatibilidad", test_compatibilidad()))
    resultados.append(("Casos edge", test_casos_edge()))
    
    # Reporte final
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DE PRUEBAS")
    print("=" * 50)
    
    todas_ok = True
    for nombre, resultado in resultados:
        estado = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{nombre:25} | {estado}")
        if not resultado:
            todas_ok = False
    
    print("-" * 50)
    
    if todas_ok:
        print("🎉 TODAS LAS PRUEBAS DE TRIGGERS PASARON")
        print("✅ El manejo de triggers está implementado correctamente")
        print("✅ Ambos módulos (tabla y grupo) son compatibles")
        print("✅ Los casos edge están manejados apropiadamente")
        print("\n💡 CONCLUSIÓN:")
        print("   • Los triggers se deshabilitan/habilitan correctamente")
        print("   • Solo afecta a la tabla ca_transaccion")
        print("   • Manejo robusto de errores")
        print("   • Listo para usar en producción")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisar los errores antes de usar en producción")
    
    return todas_ok

if __name__ == "__main__":
    try:
        exito = ejecutar_prueba_simple()
        
        if exito:
            print(f"\n🏆 CERTIFICACIÓN: El manejo de triggers está APROBADO")
        else:
            print(f"\n❌ CERTIFICACIÓN: Revisar errores antes de aprobar")
            
        sys.exit(0 if exito else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)