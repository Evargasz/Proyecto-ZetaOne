# VERSIÓN ULTRA-OPTIMIZADA DE MIGRAR_GRUPO
# Principio: INSERT DIRECTO sin validaciones innecesarias
# Acumular errores y mostrar al final

import pyodbc
import time
from tkinter import messagebox

# --- IMPORTAR FUNCIÓN DE HISTORIAL ---
from Usuario_basico.migrar_tabla import guardar_en_historial

def migrar_grupo_v2(
        grupo_conf,
        variables,
        amb_origen,
        amb_destino,
        log_func,
        progress_func,
        abort_func,
        cancelar_func=None
    ):
    """
    Migración optimizada de grupo: INSERT directo sin validaciones excesivas.
    
    Filosofía:
    1. Verificar variable en tabla principal (1 vez)
    2. Por cada tabla: SELECT con JOIN → INSERT directo
    3. Acumular errores, mostrar al final
    4. Sin dupcheck, sin desactivar índices (manejo de errores en INSERT)
    """
    log = log_func if log_func else print
    progress = progress_func if progress_func else lambda x: None
    
    def _build_conn_str(amb):
        driver = amb['driver']
        if driver == 'Sybase ASE ODBC Driver':
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={amb['ip']};"
                f"PORT={amb['puerto']};"
                f"DATABASE={amb['base']};"
                f"UID={amb['usuario']};"
                f"PWD={amb['clave'] };"
            )
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={amb['ip']},{amb['puerto']};"
            f"DATABASE={amb['base']};"
            f"UID={amb['usuario']};"
            f"PWD={amb['clave'] };"
        )
    
    conn_str_ori = _build_conn_str(amb_origen)
    conn_str_dest = _build_conn_str(amb_destino)
    tablas = grupo_conf['tablas']
    total_tablas = len(tablas)
    
    # Estadísticas
    stats = {
        'migrados': 0,
        'errores': [],  # Lista de (tabla, error, registros_fallidos)
        'skip': 0
    }
    
    t_inicio = time.time()
    log(f"\n{'='*60}")
    log(f"🚀 INICIO MIGRACIÓN GRUPO: {grupo_conf.get('grupo', 'N/A')}")
    log(f"📊 Tablas a procesar: {total_tablas}")
    log(f"🔑 Variable: {variables}")
    log(f"{'='*60}\n")
    
    try:
        with pyodbc.connect(conn_str_ori, timeout=30) as conn_ori, \
             pyodbc.connect(conn_str_dest, timeout=30, autocommit=False) as conn_dest:
            
            cur_ori = conn_ori.cursor()
            cur_dest = conn_dest.cursor()
            
            # Configurar para máximo rendimiento
            try:
                cur_ori.arraysize = 10000
                cur_dest.fast_executemany = True
            except Exception:
                pass
            
            # PASO 1: Verificar que la variable existe en tabla principal (opcional)
            # Esto se puede hacer si hay una "tabla llave" principal
            # Por ahora omitimos y confiamos en los JOINs
            
            # PASO 2: Procesar cada tabla secuencialmente
            for idx, tabla_conf in enumerate(tablas):
                if cancelar_func and cancelar_func():
                    log("❌ Migración cancelada por el usuario")
                    conn_dest.rollback()
                    break
                
                tabla = tabla_conf.get('tabla') or tabla_conf.get('tabla llave') or ''
                llave = tabla_conf.get('llave', '')
                join = tabla_conf.get('join', '')
                condicion = tabla_conf.get('condicion', '')
                
                if not tabla:
                    stats['skip'] += 1
                    continue
                
                log(f"[{idx+1}/{total_tablas}] {tabla}")
                progress(int(100 * idx / total_tablas))
                
                # Construir SELECT con o sin JOIN
                params = []
                where_clause = condicion
                
                # Reemplazar variables en condición
                if variables and where_clause:
                    import re
                    pattern = re.compile(r"(\b\w+\b)\s*=\s*'(\$\w+\$)'|(\b\w+\b)\s*=\s*(\$\w+\$)")
                    def replacer(match):
                        columna = match.group(1) or match.group(3)
                        var_placeholder = match.group(2) or match.group(4)
                        var_name = var_placeholder.strip('$')
                        if var_name in variables:
                            params.append(str(variables[var_name]))
                            return f"RTRIM(CONVERT(VARCHAR(255), {columna})) = ?"
                        return match.group(0)
                    where_clause = pattern.sub(replacer, where_clause)
                
                # Construir SQL de extracción
                if llave and join:
                    tablas_llave = [t.strip() for t in llave.split(",")]
                    if len(tablas_llave) == 1:
                        sql = f"SELECT tbl.* FROM {tabla} tbl JOIN {tablas_llave[0]} ON {join}"
                        if where_clause:
                            sql += f" WHERE {where_clause}"
                    else:
                        sql = f"SELECT tbl.* FROM {tabla} tbl"
                        for t in tablas_llave:
                            sql += f", {t}"
                        condiciones = []
                        if join:
                            condiciones.append(join)
                        if where_clause:
                            condiciones.append(where_clause)
                        if condiciones:
                            sql += " WHERE " + " AND ".join(condiciones)
                else:
                    sql = f"SELECT * FROM {tabla}"
                    if where_clause:
                        sql += f" WHERE {where_clause}"
                
                try:
                    # Desactivar governor si hay JOIN
                    if join:
                        try:
                            cur_ori.execute("SET QUERY_GOVERNOR_COST_LIMIT 0")
                        except Exception:
                            pass
                    
                    # EXTRACCIÓN
                    cur_ori.execute(sql, params if params else ())
                    filas = cur_ori.fetchall()
                    
                    if not filas:
                        log(f"  ⏭️  Sin datos")
                        stats['skip'] += 1
                        continue
                    
                    colnames = [d[0] for d in cur_ori.description]
                    log(f"  📥 Extraídos: {len(filas)} registros")
                    
                    # INSERCIÓN DIRECTA (sin dupcheck)
                    sql_insert = f"INSERT INTO {tabla} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})"
                    
                    insertados = 0
                    fallidos = 0
                    
                    # Intentar batch insert primero
                    try:
                        valores = [[getattr(row, col) for col in colnames] for row in filas]
                        cur_dest.executemany(sql_insert, valores)
                        conn_dest.commit()
                        insertados = len(filas)
                        log(f"  ✅ Insertados: {insertados}")
                    except Exception as e_batch:
                        # Si falla el batch, intentar fila por fila (ignorando duplicados)
                        conn_dest.rollback()
                        log(f"  ⚠️  Batch falló, insertando uno a uno...")
                        
                        for row in filas:
                            try:
                                valores = [getattr(row, col) for col in colnames]
                                cur_dest.execute(sql_insert, valores)
                                insertados += 1
                            except Exception as e_row:
                                msg_error = str(e_row).lower()
                                if 'duplicate' in msg_error or '2601' in msg_error or 'violation' in msg_error:
                                    fallidos += 1  # Duplicado, ignorar
                                else:
                                    fallidos += 1
                                    if fallidos == 1:  # Solo loggear primer error
                                        stats['errores'].append((tabla, str(e_row)[:100], 1))
                        
                        conn_dest.commit()
                        log(f"  ✅ Insertados: {insertados} | ⚠️  Fallidos/Duplicados: {fallidos}")
                    
                    stats['migrados'] += insertados
                    
                except Exception as e_tabla:
                    log(f"  ❌ ERROR: {str(e_tabla)[:150]}")
                    stats['errores'].append((tabla, str(e_tabla)[:200], 0))
                    try:
                        conn_dest.rollback()
                    except Exception:
                        pass
            
            progress(100)
            
    except Exception as e_global:
        log(f"\n❌ ERROR GLOBAL: {e_global}")
        return {'insertados': 0, 'omitidos': 0, 'errores': 1, 'duracion_ms': 0}
    
    # RESUMEN FINAL
    t_total_ms = int((time.time() - t_inicio) * 1000)
    
    log(f"\n{'='*60}")
    log(f"✅ RESUMEN DE MIGRACIÓN")
    log(f"{'='*60}")
    log(f"📊 Tablas procesadas: {total_tablas}")
    log(f"💾 Registros migrados: {stats['migrados']}")
    log(f"⏭️  Tablas sin datos: {stats['skip']}")
    log(f"⏱️  Duración: {t_total_ms/1000:.1f} s")
    
    if stats['errores']:
        log(f"\n⚠️  ERRORES ENCONTRADOS ({len(stats['errores'])}):")
        for tabla, error, count in stats['errores']:
            log(f"  • {tabla}: {error}")
    else:
        log(f"\n✅ Sin errores")
    
    log(f"{'='*60}\n")
    
    # Guardar en historial
    resultado = {
        'insertados': stats['migrados'],
        'omitidos': stats['skip'],
        'errores': len(stats['errores']),
        'duracion_ms': t_total_ms
    }
    
    guardar_en_historial("Grupo", grupo_conf.get('grupo', 'N/A'), resultado, base_usuario=amb_origen.get('base'))
    
    # Mensaje final
    try:
        messagebox.showinfo(
            "Migración finalizada",
            (
                f"Grupo: {grupo_conf.get('grupo','N/A')}\n"
                f"Registros migrados: {stats['migrados']}\n"
                f"Errores: {len(stats['errores'])}\n"
                f"Duración: {t_total_ms/1000:.1f} s"
            )
        )
    except Exception:
        pass
    
    return resultado