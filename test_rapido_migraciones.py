#!/usr/bin/env python3
"""
PRUEBA RÁPIDA DE MIGRACIONES
============================
Prueba simplificada para validar el funcionamiento básico del manejo de triggers
"""

import sys
import os
from unittest.mock import Mock

# Agregar Usuario_basico al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Usuario_basico'))

def test_manage_trigger():
    """Prueba básica de _manage_trigger"""
    print("🧪 Probando _manage_trigger...")
    
    try:
        from migrar_tabla import _manage_trigger
        
        # Test 1: ca_transaccion con DISABLE
        mock_cursor = Mock()
        mock_log = Mock()
        
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        
        # Verificar que se ejecutó el SQL correcto
        mock_cursor.execute.assert_called_with("ALTER TABLE ca_transaccion DISABLE TRIGGER tg_ca_transaccion")
        print("  ✅ DISABLE trigger - OK")
        
        # Test 2: ca_transaccion con ENABLE
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "ca_transaccion", "ENABLE", mock_log)
        
        mock_cursor.execute.assert_called_with("ALTER TABLE ca_transaccion ENABLE TRIGGER tg_ca_transaccion")
        print("  ✅ ENABLE trigger - OK")
        
        # Test 3: Otra tabla (no debería hacer nada)
        mock_cursor.reset_mock()
        _manage_trigger(mock_cursor, "otra_tabla", "DISABLE", mock_log)
        
        mock_cursor.execute.assert_not_called()
        print("  ✅ Otras tablas ignoradas - OK")
        
        # Test 4: Manejo de errores
        mock_cursor.reset_mock()
        mock_cursor.execute.side_effect = Exception("Error SQL")
        
        _manage_trigger(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        print("  ✅ Manejo de errores - OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_imports():
    """Prueba que los módulos se importen correctamente"""
    print("📦 Probando importaciones...")
    
    try:
        from migrar_tabla import _manage_trigger, migrar_tabla_secuencial
        print("  ✅ migrar_tabla.py - OK")
        
        from migrar_grupo import _manage_trigger as _manage_trigger_grupo, migrar_tabla_del_grupo
        print("  ✅ migrar_grupo.py - OK")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_funciones_existen():
    """Verifica que las funciones críticas existan"""
    print("🔍 Verificando funciones críticas...")
    
    try:
        from migrar_tabla import _manage_trigger, migrar_tabla_secuencial, migrar_tabla
        from migrar_grupo import migrar_tabla_del_grupo
        
        # Verificar que las funciones son callable
        assert callable(_manage_trigger), "_manage_trigger no es callable"
        assert callable(migrar_tabla_secuencial), "migrar_tabla_secuencial no es callable"
        assert callable(migrar_tabla), "migrar_tabla no es callable"
        assert callable(migrar_tabla_del_grupo), "migrar_tabla_del_grupo no es callable"
        
        print("  ✅ Todas las funciones críticas existen - OK")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_compatibilidad_triggers():
    """Prueba compatibilidad del manejo de triggers entre módulos"""
    print("🔄 Probando compatibilidad entre módulos...")
    
    try:
        from migrar_tabla import _manage_trigger as trigger_tabla
        from migrar_grupo import _manage_trigger as trigger_grupo
        
        mock_cursor = Mock()
        mock_log = Mock()
        
        # Ambas funciones deberían comportarse igual
        trigger_tabla(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        call_tabla = mock_cursor.execute.call_args
        
        mock_cursor.reset_mock()
        trigger_grupo(mock_cursor, "ca_transaccion", "DISABLE", mock_log)
        call_grupo = mock_cursor.execute.call_args
        
        assert call_tabla == call_grupo, "Comportamiento inconsistente entre módulos"
        
        print("  ✅ Compatibilidad entre módulos - OK")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def ejecutar_prueba_rapida():
    """Ejecuta todas las pruebas rápidas"""
    print("🚀 PRUEBA RÁPIDA DE MIGRACIONES")
    print("=" * 50)
    
    resultados = []
    
    # Ejecutar pruebas
    resultados.append(("Importaciones", test_imports()))
    resultados.append(("Funciones críticas", test_funciones_existen()))
    resultados.append(("Manejo de triggers", test_manage_trigger()))
    resultados.append(("Compatibilidad", test_compatibilidad_triggers()))
    
    # Reporte final
    print("\n" + "=" * 50)
    print("📊 RESULTADOS")
    print("=" * 50)
    
    todas_ok = True
    for nombre, resultado in resultados:
        estado = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{nombre:20} | {estado}")
        if not resultado:
            todas_ok = False
    
    print("-" * 50)
    
    if todas_ok:
        print("🎉 TODAS LAS PRUEBAS BÁSICAS PASARON")
        print("✅ El manejo de triggers está funcionando correctamente")
        print("✅ Los módulos están listos para usar")
        print("\n💡 Para pruebas más exhaustivas, ejecuta:")
        print("   cd Usuario_basico")
        print("   python ejecutar_todas_las_pruebas.py")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisar los errores antes de usar en producción")
    
    return todas_ok

if __name__ == "__main__":
    try:
        exito = ejecutar_prueba_rapida()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        sys.exit(1)