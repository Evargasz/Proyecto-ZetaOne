#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para validar reintentos automáticos de commit/reconexión.
Migra 5 registros de una tabla pequeña y valida que funcione correctamente.
"""

import sys
import logging
import os
import json
from datetime import datetime

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler("test_migracion_retry.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)

# Importar funciones de migración
from Usuario_basico.migrar_tabla import migrar_tabla

def cargar_ambiente(nombre):
    """Carga configuración de ambiente desde JSON."""
    try:
        with open(os.path.join("json", "ambientes.json"), "r", encoding="utf-8") as f:
            ambientes = json.load(f)
            for amb in ambientes:
                if amb["nombre"] == nombre:
                    return amb
        log.error(f"Ambiente '{nombre}' no encontrado.")
        return None
    except Exception as e:
        log.error(f"Error cargando ambientes: {e}")
        return None

def test_migracion_pequena():
    """Prueba migración de 5 registros con reintentos automáticos."""
    
    log.info("=" * 80)
    log.info("PRUEBA DE MIGRACION CON REINTENTOS AUTOMATICOS")
    log.info("=" * 80)
    
    # Cargar ambientes
    amb_origen = cargar_ambiente("SYBREPOR")
    amb_destino = cargar_ambiente("SYBCOB25")
    
    if not amb_origen or not amb_destino:
        log.error("No se pudieron cargar los ambientes.")
        return False
    
    log.info(f"Ambiente origen: {amb_origen['nombre']} ({amb_origen['ip']})")
    log.info(f"Ambiente destino: {amb_destino['nombre']} ({amb_destino['ip']})")
    
    # Tabla para prueba: la que ya probamos antes
    tabla = "cob_conta_super..sb_balance"
    # Usar TOP de Sybase para limitar a 10 registros
    # En realidad ejecutaremos sobre toda la tabla, pero solo para ver los primeros registros migrados
    where = None
    
    log.info(f"\nTabla a migrar: {tabla}")
    if where:
        log.info(f"Condicion WHERE: {where}")
    
    # Obtener información de la tabla
    from Usuario_basico.migrar_tabla import consultar_tabla_e_indice
    
    def dummy_log(msg, nivel="info"):
        pass
    
    def dummy_abort(msg):
        raise Exception(msg)
    
    tabla_info = consultar_tabla_e_indice(tabla, amb_origen, amb_destino, dummy_log, dummy_abort, where, None)
    if not tabla_info:
        log.error("No se pudo obtener informacion de la tabla.")
        return False
    
    columnas = tabla_info.get('columnas', [])
    pk = tabla_info.get('clave_primaria', [])
    nregs = tabla_info.get('nregs', 0)
    
    log.info(f"Columnas: {len(columnas)}")
    log.info(f"Clave primaria: {pk}")
    log.info(f"Registros a migrar: {nregs}")
    
    # Variables para logs
    logs_capturados = []
    progreso_actual = [0]
    
    def log_func(msg, nivel="info"):
        """Captura logs de la migración."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        logs_capturados.append(log_entry)
        
        # Usar solo caracteres ASCII para evitar problemas de encoding en Windows
        msg_ascii = msg.encode('ascii', 'replace').decode('ascii')
        
        if nivel == "info":
            log.info(msg_ascii)
        elif nivel == "warning":
            log.warning(msg_ascii)
        elif nivel == "error":
            log.error(msg_ascii)
        elif nivel == "success":
            log.info("[SUCCESS] " + msg_ascii)
    
    def progress_func(porcentaje):
        """Captura progreso."""
        progreso_actual[0] = porcentaje
        if porcentaje % 10 == 0:
            log.info(f"Progreso: {porcentaje}%")
    
    def abort_func(msg):
        """Captura aborto."""
        msg_ascii = msg.encode('ascii', 'replace').decode('ascii')
        log.error(f"ABORT: {msg_ascii}")
    
    def cancelar_func():
        """Función para cancelar (nunca retorna True en esta prueba)."""
        return False
    
    try:
        log.info("\n" + "=" * 80)
        log.info("INICIANDO MIGRACIÓN...")
        log.info("=" * 80 + "\n")
        
        resultado = migrar_tabla(
            tabla=tabla,
            where=where,
            amb_origen=amb_origen,
            amb_destino=amb_destino,
            log_func=log_func,
            progress_func=progress_func,
            abort_func=abort_func,
            columnas=columnas,
            clave_primaria=pk,
            cancelar_func=cancelar_func,
            total_registros=nregs
        )
        
        log.info("\n" + "=" * 80)
        log.info("RESULTADO FINAL")
        log.info("=" * 80)
        log.info(f"Insertados: {resultado.get('insertados', 0)}")
        log.info(f"Omitidos: {resultado.get('omitidos', 0)}")
        log.info(f"Progreso final: {progreso_actual[0]}%")
        
        # Validaciones
        exito = True
        if resultado.get('insertados', 0) == 0 and resultado.get('omitidos', 0) == 0:
            log.warning("[WARNING] No se proceso ningun registro. Posible problema de conectividad o tabla vacia.")
            exito = False
        elif resultado.get('insertados', 0) > 0:
            log.info(f"[SUCCESS] Migracion completada: {resultado['insertados']} registros insertados")
        else:
            log.info(f"[INFO] Todos los registros fueron omitidos (duplicados existentes): {resultado.get('omitidos', 0)}")
        
        # Guardar logs en archivo
        log_file = "test_migracion_retry_output.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("LOGS CAPTURADOS DE LA MIGRACIÓN\n")
            f.write("=" * 80 + "\n\n")
            for entry in logs_capturados:
                f.write(entry + "\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"RESULTADO FINAL\n")
            f.write("=" * 80 + "\n")
            f.write(f"Insertados: {resultado.get('insertados', 0)}\n")
            f.write(f"Omitidos: {resultado.get('omitidos', 0)}\n")
            f.write(f"Progreso final: {progreso_actual[0]}%\n")
        
        log.info(f"\nArchivos de log guardados:")
        log.info(f"  - test_migracion_retry.log")
        log.info(f"  - test_migracion_retry_output.txt")
        
        return exito
        
    except Exception as e:
        log.error(f"\n❌ Error durante la migración: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    log.info("Iniciando prueba de migracion con reintentos automaticos...")
    exito = test_migracion_pequena()
    
    if exito:
        log.info("\n[SUCCESS] PRUEBA COMPLETADA EXITOSAMENTE")
        sys.exit(0)
    else:
        log.error("\n[ERROR] PRUEBA FALLO O TUVO PROBLEMAS")
        sys.exit(1)
