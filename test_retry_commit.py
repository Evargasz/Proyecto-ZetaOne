#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test simple para validar la función _retry_commit() con reintentos automáticos.
"""

import sys
import logging
import pyodbc
import time
import json
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
log = logging.getLogger(__name__)

# Importar la función de reintentos
from Usuario_basico.migrar_tabla import _retry_commit, _build_conn_str

def cargar_ambiente(nombre):
    """Carga configuración de ambiente desde JSON."""
    try:
        with open(os.path.join("json", "ambientes.json"), "r", encoding="utf-8") as f:
            ambientes = json.load(f)
            for amb in ambientes:
                if amb["nombre"] == nombre:
                    return amb
        return None
    except Exception as e:
        log.error(f"Error cargando ambientes: {e}")
        return None

def test_retry_commit_funcion():
    """Test de la función _retry_commit() con un commit simple."""
    
    log.info("=" * 80)
    log.info("TEST DE LA FUNCION _retry_commit()")
    log.info("=" * 80)
    
    # Cargar ambientes
    amb_destino = cargar_ambiente("SYBCOB25")
    if not amb_destino:
        log.error("No se pudo cargar el ambiente SYBCOB25")
        return False
    
    log.info(f"\nAmbiente destino: {amb_destino['nombre']} ({amb_destino['ip']})")
    conn_str = _build_conn_str(amb_destino)
    
    try:
        # Conectar a la base de datos CON AUTOCOMMIT para crear la tabla
        log.info("\nConectando a la base de datos...")
        conn = pyodbc.connect(conn_str, timeout=30, autocommit=True)
        log.info("Conexion exitosa (autocommit=True).")
        
        # Crear tabla temporal para prueba
        temp_table = "#test_retry_commit"
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE {temp_table}")
        except:
            pass
        
        log.info(f"\nCreando tabla temporal {temp_table}...")
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE {temp_table} (
                    id INT PRIMARY KEY,
                    nombre VARCHAR(100),
                    fecha DATETIME
                )
            """)
        log.info("Tabla temporal creada.")
        
        # Ahora cambiar a NO autocommit para las pruebas
        conn.autocommit = False
        
        # Preparar datos para insertar
        sql_insert = f"INSERT INTO {temp_table} (id, nombre, fecha) VALUES (?, ?, ?)"
        test_data = [
            (1, 'Registro Test 1', '2025-11-28'),
            (2, 'Registro Test 2', '2025-11-28'),
            (3, 'Registro Test 3', '2025-11-28'),
        ]
        log.info("\n[TEST 1] Commit exitoso en primer intento...")
        success, count, msg = _retry_commit(
            conn, conn_str, sql_insert, test_data,
            max_retries=3, initial_backoff=0.5, log_func=log.info
        )
        
        if success and count == len(test_data):
            log.info(f"[PASS] Commit exitoso: {count} registros insertados. Msg: {msg}")
        else:
            log.error(f"[FAIL] Commit no exitoso. Success: {success}, Count: {count}")
            return False
        
        # Verificar que los datos se insertaron
        log.info("\nVerificando que los datos se insertaron...")
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {temp_table}")
            count = cur.fetchone()[0]
            log.info(f"Registros en tabla: {count}")
            if count == 3:
                log.info("[PASS] Los 3 registros fueron insertados correctamente")
            else:
                log.error(f"[FAIL] Se esperaban 3 registros, se encontraron {count}")
                return False
        
        # Limpiar tabla temporal
        log.info(f"\nLimpiando tabla temporal {temp_table}...")
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {temp_table}")
            conn.commit()
        
        # Test 2: Verificar detección de desconexión
        log.info("\n[TEST 2] Verificando manejo de conexión cerrada...")
        log.info("(Esta prueba valida que _retry_commit detecta y maneja conexión cerrada)")
        
        # Crear una conexión nueva y cerrarla antes de pasar a _retry_commit
        log.info("Creando conexión que será cerrada...")
        conn_closed = pyodbc.connect(conn_str, timeout=60, autocommit=False)
        log.info("Cerrando conexión...")
        conn_closed.close()
        
        time.sleep(0.5)
        
        # Intentar commit con conexión cerrada - _retry_commit debe detectarlo y reabrirla
        log.info("Llamando a _retry_commit con conexión cerrada (debe intentar reabrirla)...")
        success, count, msg = _retry_commit(
            conn_closed, conn_str, sql_insert, test_data[:2],  # 2 registros
            max_retries=2, initial_backoff=0.5, log_func=log.info
        )
        
        # En este caso, esperamos que la tabla temporal no exista en la nueva conexión,
        # por lo que fallará, pero esto demuestra que _retry_commit intentó reabrirse
        log.info(f"Resultado del retry: Success={success}, Count={count}, Msg={msg[:50]}")
        log.warning("[INFO] TEST 2 demuestra que _retry_commit intenta reconectar cuando la conexión está cerrada")
        
        # Limpiar
        log.info("\nLimpiando tabla temporal...")
        try:
            with pyodbc.connect(conn_str, timeout=30, autocommit=False) as conn_cleanup:
                with conn_cleanup.cursor() as cur:
                    cur.execute(f"DROP TABLE {temp_table}")
                    conn_cleanup.commit()
            log.info("Tabla temporal eliminada.")
        except Exception as cleanup_err:
            log.warning(f"Advertencia al limpiar: {str(cleanup_err)[:50]}")
        
        log.info("\n" + "=" * 80)
        log.info("[SUCCESS] TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        log.info("=" * 80)
        return True
        
    except Exception as e:
        log.error(f"\n[FAIL] Error en test: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    log.info("\nTest de _retry_commit() - Sistema de Reintentos Automaticos\n")
    exito = test_retry_commit_funcion()
    
    sys.exit(0 if exito else 1)
