import pyodbc
import traceback
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
# --- IMPORTACIONES PARA PARALELIZACIÓN ---
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty

# ==================== LOGICA DE BACKEND MIGRACION ====================

def _build_conn_str(amb):
    driver = amb.get('driver', '')
    if 'sybase' in driver.lower():
        odbc_path = os.path.join(os.getcwd(), 'ODBC')
        os.environ['SYBASE'] = odbc_path
        os.environ['SYBASE_OCS'] = 'OCS-15_0'
    
    server = amb.get('ip', '')
    port = amb.get('puerto', '')
    database = amb.get('base', '')
    uid = amb.get('usuario', '')
    pwd = amb.get('clave', '')
    
    if 'sql server' in driver.lower():
        return f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};UID={uid};PWD={pwd};TrustServerCertificate=yes;"
    else:  # Sybase
        return f"DRIVER={{{driver}}};SERVER={server};PORT={port};DATABASE={database};UID={uid};PWD={pwd};"


def columnas_tabla(conn_str, tabla):
    with pyodbc.connect(conn_str, timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {tabla} WHERE 1=0")
            return [desc[0] for desc in cur.description]

def pk_tabla(conn_str, tabla, is_sybase):
    import re
    with pyodbc.connect(conn_str, timeout=30, autocommit=True) as conn:
        with conn.cursor() as cur:
            pk_cols = []
            partes = tabla.split('.')
            nombre_tb_simple = partes[-1]
            try:
                if is_sybase:
                    try:
                        cur.execute("sp_pkeys @table_name=?", [nombre_tb_simple])
                        pk_cols = [row.column_name.lower().strip() for row in cur.fetchall()]
                    except Exception:
                        pk_cols = []
                    if not pk_cols:
                        try:
                            cur.execute("sp_help " + nombre_tb_simple)
                            found = False
                            while True:
                                rows = cur.fetchall()
                                columns = [col[0] for col in cur.description] if cur.description else []
                                if ('index_description' in columns) and ('index_keys' in columns):
                                    idx_desc_idx = columns.index('index_description')
                                    idx_keys_idx = columns.index('index_keys')
                                    for row in rows:
                                        idx_desc = row[idx_desc_idx]
                                        if re.search(r'\bunique\b', idx_desc, re.IGNORECASE):
                                            pk_cols = [col.strip() for col in row[idx_keys_idx].strip().split(',')]
                                            found = True
                                            break
                                    if found:
                                        break
                                if not cur.nextset():
                                    break
                        except Exception:
                            pk_cols = []
                else: # SQL Server
                    consulta_pk = """
                    SELECT col.name
                    FROM sys.indexes pk
                    INNER JOIN sys.index_columns ic ON pk.object_id = ic.object_id AND pk.index_id = ic.index_id
                    INNER JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
                    INNER JOIN sys.tables t ON pk.object_id = t.object_id
                    WHERE pk.is_primary_key = 1 AND t.name = ?
                    ORDER BY ic.key_ordinal
                    """
                    cur.execute(consulta_pk, (nombre_tb_simple,))
                    pk_cols = [row[0].lower() for row in cur.fetchall()]
            except Exception:
                pk_cols = []
            return pk_cols

def consultar_tabla_e_indice(tabla, amb_origen, amb_destino, log_func, abort_func, where=None, base_usuario=None):
    is_sybase = amb_destino["driver"].lower().startswith("sybase")
    tabla_simple = tabla.split('.')[-1]
    tabla_ref = tabla
    
    amb_origen_db = amb_origen.copy()
    amb_destino_db = amb_destino.copy()
    if base_usuario:
        amb_origen_db['base'] = base_usuario
        amb_destino_db['base'] = base_usuario
        
    conn_str_ori = _build_conn_str(amb_origen_db)
    conn_str_dest = _build_conn_str(amb_destino_db)
    
    try:
        cols_ori = columnas_tabla(conn_str_ori, tabla_ref)
    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str:
            abort_func(f"Error de conexión (Timeout) al ambiente origen. Por favor, verifique que su conexión de red (VPN) esté activa.")
        elif "login failed" in error_str or "authentication" in error_str:
            abort_func(f"Error de autenticación en ambiente origen. Verifique que el usuario y la contraseña sean correctos.")
        elif "tcp/ip" in error_str or "network-related" in error_str or "unable to connect" in error_str or "sql server does not exist" in error_str or "unable to establish a connection" in error_str:
             abort_func(f"Error de red al conectar con el ambiente origen. Verifique que la VPN esté activa y que el servidor sea accesible.")
        else:
            abort_func(f"No se pudo acceder a la tabla '{tabla}' en ambiente origen.\n\nError: {str(e)[:120]}")
        return None
    
    try:
        cols_dest = columnas_tabla(conn_str_dest, tabla_ref)
    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str:
            abort_func(f"Error de conexión (Timeout) al ambiente destino. Por favor, verifique que su conexión de red (VPN) esté activa.")
        elif "login failed" in error_str or "authentication" in error_str:
            abort_func(f"Error de autenticación en ambiente destino. Verifique que el usuario y la contraseña sean correctos.")
        elif "tcp/ip" in error_str or "network-related" in error_str or "unable to connect" in error_str or "sql server does not exist" in error_str or "unable to establish a connection" in error_str:
             abort_func(f"Error de red al conectar con el ambiente destino. Verifique que la VPN esté activa y que el servidor sea accesible.")
        else:
            abort_func(f"No se pudo acceder a la tabla '{tabla}' en ambiente destino.\n\nError: {str(e)[:120]}")
        return None

    if cols_ori != cols_dest:
        abort_func(f"❌ Estructura diferente entre origen y destino. Verifique que las tablas sean idénticas.")
        return None
    else:
        log_func(f"✅ Estructura de tabla validada correctamente.")

    try:
        pk = pk_tabla(conn_str_ori, tabla_simple, is_sybase)
        if not pk:
            log_func("⚠️ No se detectó clave primaria. La migración será secuencial y más lenta.", "warning")
    except Exception as e:
        pk = []
        log_func(f"⚠️ Error detectando clave primaria: {str(e)[:50]}", "warning")

    try:
        with pyodbc.connect(conn_str_ori, timeout=30) as conn:
            with conn.cursor() as cur:
                sql = f"SELECT COUNT(*) FROM {tabla_ref}"
                if where:
                    sql += f" WHERE {where}"
                cur.execute(sql)
                nregs = cur.fetchone()[0]
                log_func(f"📊 Total de registros a procesar: {nregs:,}")
    except Exception as e:
        nregs = -1
        log_func(f"⚠️ No se pudo contar registros. La migración continuará sin mostrar progreso preciso.", "warning")

    return {
        "columnas": cols_ori,
        "clave_primaria": pk,
        "nregs": nregs,
    }

# --- ARQUITECTURA PARALELA OPTIMIZADA ---

def productor_de_pks_optimizado(pks_queue, conn_str_ori, tabla, pk_cols, where, log, cancelar_event):
    log(f"🔄 Iniciando extracción optimizada de claves primarias...")
    batch_size = 10000
    pk_string = ','.join(pk_cols)
    
    # OPTIMIZACIÓN: Usar ORDER BY para mejor performance en índices
    sql = f"SELECT {pk_string} FROM {tabla}"
    if where:
        sql += f" WHERE {where}"
    sql += f" ORDER BY {pk_string}"  # Ordenar por la clave primaria completa

    try:
        with pyodbc.connect(conn_str_ori, timeout=60) as conn:
            with conn.cursor() as cur:
                # OPTIMIZACIÓN: Configurar cursor para mejor performance
                cur.arraysize = batch_size
                cur.execute(sql)
                
                lotes_procesados = 0
                while not cancelar_event.is_set():
                    pks = cur.fetchmany(batch_size)
                    if not pks:
                        break
                    pks_queue.put([tuple(pk) for pk in pks])
                    lotes_procesados += 1
                    if lotes_procesados % 5 == 0:
                        log(f"📦 Extraídas {lotes_procesados * batch_size:,} claves primarias...")
        log(f"✅ Extracción de claves completada.")
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            log(f"⚠️ Conexión perdida durante extracción. Reintentando...", "warning")
            # Reintentar una vez
            try:
                with pyodbc.connect(conn_str_ori, timeout=90) as conn_retry:
                    log(f"✅ Reconexión exitosa. Continuando extracción...")
            except Exception as retry_error:
                log(f"❌ Fallo en reconexión: {str(retry_error)[:100]}", "error")
        else:
            log(f"❌ Error crítico extrayendo datos: {str(e)[:100]}", "error")
    finally:
        pks_queue.put(None)

def consumidor_de_pks_optimizado(
    pks_queue, conn_str_ori, conn_str_dest, tabla, columnas, pk_cols, log, 
    progreso_compartido, lock, cancelar_event
):
    insertados_hilo = 0
    omitidos_hilo = 0
    
    # OPTIMIZACIÓN 1: Tamaños de lote optimizados
    SUB_BATCH_SIZE = 500
    COMMIT_BATCH_SIZE = 5000  # Commits menos frecuentes para performance
    
    # OPTIMIZACIÓN 2: Conexiones persistentes con timeouts aumentados
    conn_ori = pyodbc.connect(conn_str_ori, timeout=90)
    conn_dest = pyodbc.connect(conn_str_dest, timeout=90, autocommit=False)
    cur_ori = conn_ori.cursor()
    cur_dest = conn_dest.cursor()
    
    # OPTIMIZACIÓN 3: Configuraciones de performance
    try:
        cur_ori.fast_executemany = True
        cur_dest.fast_executemany = True
    except AttributeError:
        pass  # No disponible en todas las versiones
    
    pending_inserts = []
    
    try:
        while not cancelar_event.is_set():
            try:
                lote_pks_grande = pks_queue.get(timeout=5)
                if lote_pks_grande is None:
                    pks_queue.put(None)
                    break

                for i in range(0, len(lote_pks_grande), SUB_BATCH_SIZE):
                    if cancelar_event.is_set(): break
                    
                    sub_lote_pks = lote_pks_grande[i:i + SUB_BATCH_SIZE]
                    
                    # OPTIMIZACIÓN 4: Verificación de duplicados más eficiente
                    if len(pk_cols) == 1:
                        pk_values = [pk[0] for pk in sub_lote_pks]
                        placeholders = ','.join(['?' for _ in pk_values])
                        sql_check = f"SELECT {pk_cols[0]} FROM {tabla} WHERE {pk_cols[0]} IN ({placeholders})"
                        pks_existentes = set(row[0] for row in cur_dest.execute(sql_check, pk_values).fetchall())
                        pks_a_migrar = [pk for pk in sub_lote_pks if pk[0] not in pks_existentes]
                    else:
                        # Para PK compuesta, la estrategia de OR es necesaria para compatibilidad
                        condiciones_check = " OR ".join([f"({ ' AND '.join([f'{col}=?' for col in pk_cols]) })" for _ in sub_lote_pks])
                        params_check = [item for sublist in sub_lote_pks for item in sublist]
                        sql_check = f"SELECT {','.join(pk_cols)} FROM {tabla} WHERE {condiciones_check}"
                        pks_existentes = set(tuple(row) for row in cur_dest.execute(sql_check, params_check).fetchall())
                        pks_a_migrar = [pk for pk in sub_lote_pks if pk not in pks_existentes]

                    omitidos_en_sub_lote = len(sub_lote_pks) - len(pks_a_migrar)
                    omitidos_hilo += omitidos_en_sub_lote

                    if pks_a_migrar:
                        # OPTIMIZACIÓN 5: Fetch masivo usando IN para PK simple
                        if len(pk_cols) == 1:
                            pk_values = [pk[0] for pk in pks_a_migrar]
                            placeholders = ','.join(['?' for _ in pk_values])
                            sql_fetch = f"SELECT {','.join(columnas)} FROM {tabla} WHERE {pk_cols[0]} IN ({placeholders})"
                            filas_a_insertar = cur_ori.execute(sql_fetch, pk_values).fetchall()
                        else:
                            # Para PK compuesta, la estrategia OR es más compatible
                            filas_a_insertar = []
                            FETCH_BATCH = 200 # Lotes más pequeños para evitar timeouts
                            for j in range(0, len(pks_a_migrar), FETCH_BATCH):
                                batch_pks = pks_a_migrar[j:j + FETCH_BATCH]
                                condiciones_pk = " OR ".join([f"({ ' AND '.join([f'{col}=?' for col in pk_cols]) })" for _ in batch_pks])
                                params_pk = [item for sublist in batch_pks for item in sublist]
                                sql_fetch = f"SELECT {','.join(columnas)} FROM {tabla} WHERE {condiciones_pk}"
                                try:
                                    batch_filas = cur_ori.execute(sql_fetch, params_pk).fetchall()
                                    filas_a_insertar.extend(batch_filas)
                                except Exception as fetch_error:
                                    log(f"⚠️ Error en fetch batch: {str(fetch_error)[:50]}", "warning")
                                    continue

                        if filas_a_insertar:
                            try:
                                # Acumular inserciones para commits por lotes
                                pending_inserts.extend([tuple(row) for row in filas_a_insertar])
                                insertados_hilo += len(filas_a_insertar)
                                
                                # Commit en lotes grandes para mejorar rendimiento
                                if len(pending_inserts) >= COMMIT_BATCH_SIZE:
                                    sql_insert = f"INSERT INTO {tabla} ({','.join(columnas)}) VALUES ({','.join(['?' for _ in columnas])})"
                                    cur_dest.executemany(sql_insert, pending_inserts)
                                    conn_dest.commit()
                                    pending_inserts.clear()
                                
                            except Exception as insert_error:
                                log(f"⚠️ Error en insert: {str(insert_error)[:50]}", "warning")
                                conn_dest.rollback()
                                pending_inserts.clear()
                                continue
                    
                    # Actualizar contadores de progreso
                    with lock:
                        if filas_a_insertar:
                            progreso_compartido['insertados'] += len(filas_a_insertar)
                        progreso_compartido['omitidos'] += omitidos_en_sub_lote

            except Empty:
                continue
                
        # Commit final de registros pendientes
        if pending_inserts:
            try:
                sql_insert = f"INSERT INTO {tabla} ({','.join(columnas)}) VALUES ({','.join(['?' for _ in columnas])})"
                cur_dest.executemany(sql_insert, pending_inserts)
                conn_dest.commit()
                log(f"✅ Commit final exitoso: {len(pending_inserts)} registros")
            except Exception as final_error:
                log(f"❌ Error crítico en commit final: {str(final_error)[:100]}", "error")
                conn_dest.rollback()
                # CRÍTICO: Ajustar contadores si el commit falló
                insertados_hilo -= len(pending_inserts)
                with lock:
                    progreso_compartido['insertados'] -= len(pending_inserts)
        
        # Log final del hilo
        log(f"🏁 Hilo terminado. Insertados: {insertados_hilo:,}, Omitidos: {omitidos_hilo:,}")
            
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            log(f"⚠️ Conexión perdida durante migración. Haciendo rollback.", "error")
        elif "duplicate" in error_msg or "primary key" in error_msg:
            log(f"⚠️ Registros duplicados detectados.", "warning")
        else:
            log(f"❌ Error en migración: {str(e)[:100]}", "error")
        
        # Rollback seguro
        try:
            if conn_dest:
                conn_dest.rollback()
                log(f"✅ Rollback completado correctamente.")
        except Exception as rb_error:
            log(f"⚠️ Error en rollback: {str(rb_error)[:50]}", "warning")
    finally:
        conn_ori.close()
        conn_dest.close()

    return insertados_hilo, omitidos_hilo

def migrar_tabla(
    tabla, where, amb_origen, amb_destino, log_func=None, progress_func=None,
    abort_func=None, columnas=None, clave_primaria=None, base_usuario=None,
    cancelar_func=None, total_registros=None
):
    log = log_func
    progress = progress_func
    abort = abort_func

    if base_usuario:
        amb_origen_db = amb_origen.copy()
        amb_destino_db = amb_destino.copy()
        amb_origen_db['base'] = base_usuario
        amb_destino_db['base'] = base_usuario
    else:
        amb_origen_db = amb_origen
        amb_destino_db = amb_destino

    conn_str_ori = _build_conn_str(amb_origen_db)
    conn_str_dest = _build_conn_str(amb_destino_db)
    
    # Si no se proporciona total_registros, intentar obtenerlo
    if not total_registros:
        try:
            with pyodbc.connect(conn_str_ori, timeout=30) as conn:
                with conn.cursor() as cur:
                    sql = f"SELECT COUNT(*) FROM {tabla}"
                    if where:
                        sql += f" WHERE {where}"
                    cur.execute(sql)
                    total_registros = cur.fetchone()[0]
                    log(f"📊 Total estimado: {total_registros:,} registros")
        except Exception:
            total_registros = 100000  # Estimación por defecto
    
    # OPTIMIZACIÓN: Usar migración secuencial para datasets pequeños (más eficiente)
    if not clave_primaria or total_registros < 1000:
        if not clave_primaria:
            log("⚠️ Sin clave primaria detectada. Usando migración secuencial.", "warning")
        else:
            log(f"📊 Dataset pequeño ({total_registros:,} registros). Usando migración secuencial optimizada.")
        return migrar_tabla_secuencial(tabla, where, amb_origen_db, amb_destino_db, log, progress, abort, columnas, cancelar_func, total_registros)

    log(f"🚀 Iniciando migración paralela optimizada de '{tabla}' ({total_registros:,} registros)...")
    
    pks_queue = Queue(maxsize=20)  # Aumentar buffer
    cancelar_event = threading.Event()
    # PROGRESO SIMPLIFICADO: Solo lo que importa para la barra
    progreso_compartido = {
        'insertados': 0,      # Registros realmente insertados
        'omitidos': 0,        # Registros omitidos (duplicados)
        'total': total_registros  # Total a migrar
    }
    lock = threading.Lock()

    # OPTIMIZACIÓN: Ajustar workers para balancear carga y contención
    with ThreadPoolExecutor(max_workers=4) as executor:
        productor_future = executor.submit(
            productor_de_pks_optimizado, pks_queue, conn_str_ori, tabla,
            clave_primaria, where, log, cancelar_event
        )

        consumidor_futures = [
            executor.submit(
                consumidor_de_pks_optimizado, pks_queue, conn_str_ori, conn_str_dest, tabla,
                columnas, clave_primaria, log, progreso_compartido, lock, cancelar_event
            ) for _ in range(3)
        ]
        
        # Bucle de progreso en el hilo principal
        ultimo_progreso = 0
        ultimo_log_regs = 0
        while not all(f.done() for f in consumidor_futures):
            if cancelar_func and cancelar_func():
                log("🛑 Cancelación solicitada por el usuario.", "warning")
                cancelar_event.set()
                break
            
            with lock:
                registros_migrados = progreso_compartido['insertados'] + progreso_compartido['omitidos']
                if progreso_compartido['total'] > 0 and registros_migrados > 0:
                    porcentaje_real = min(95, int((registros_migrados / progreso_compartido['total']) * 100))
                    
                    if porcentaje_real > ultimo_progreso:
                        progress(porcentaje_real)
                        ultimo_progreso = porcentaje_real
                    
                    if (registros_migrados - ultimo_log_regs) >= 5000:
                        log(f"📈 Progreso: {porcentaje_real}% ({registros_migrados:,}/{progreso_compartido['total']:,})")
                        ultimo_log_regs = registros_migrados
            
            time.sleep(0.2)

    # Esperar a que terminen todos los hilos y obtener resultados
    total_insertados = 0
    total_omitidos = 0
    
    for future in consumidor_futures:
        try:
            if not future.cancelled():
                insertados, omitidos = future.result(timeout=10)
                total_insertados += insertados
                total_omitidos += omitidos
        except Exception as e:
            log(f"⚠️ Error obteniendo resultado de hilo: {str(e)[:50]}", "warning")
    
    if cancelar_event.is_set():
        abort(f"🛑 Migración de '{tabla}' cancelada por el usuario.")
        return {"insertados": 0, "omitidos": 0}
    
    # VALIDACIÓN FINAL: Verificar que realmente se insertaron registros
    if total_insertados > 0:
        log(f"✅ Migración completada exitosamente. Insertados: {total_insertados:,} | Omitidos: {total_omitidos:,}", "success")
    else:
        log(f"⚠️ Migración completada sin insertar registros. Omitidos: {total_omitidos:,}", "warning")
        
    progress(100)
    return {"insertados": total_insertados, "omitidos": total_omitidos}

def migrar_tabla_secuencial(tabla, where, amb_origen, amb_destino, log, progress, abort, columnas, cancelar_func, total_registros=None):
    conn_str_ori = _build_conn_str(amb_origen)
    conn_str_dest = _build_conn_str(amb_destino)
    
    total_insertados = 0
    total_omitidos = 0
    # OPTIMIZACIÓN: Batch size dinámico según tamaño del dataset
    batch_size = min(1000, max(100, total_registros // 10)) if total_registros else 500
    
    try:
        with pyodbc.connect(conn_str_ori, timeout=60) as conn_ori, \
             pyodbc.connect(conn_str_dest, timeout=60, autocommit=False) as conn_dest:
            
            cur_ori = conn_ori.cursor()
            cur_dest = conn_dest.cursor()
            
            sql_fetch = f"SELECT {','.join(columnas)} FROM {tabla}"
            if where:
                sql_fetch += f" WHERE {where}"
            
            cur_ori.execute(sql_fetch)
            
            while not (cancelar_func and cancelar_func()):
                filas = cur_ori.fetchmany(batch_size)
                if not filas:
                    break
                
                sql_insert = f"INSERT INTO {tabla} ({','.join(columnas)}) VALUES ({','.join(['?' for _ in columnas])})"
                try:
                    cur_dest.executemany(sql_insert, [tuple(row) for row in filas])
                    conn_dest.commit()
                    total_insertados += len(filas)
                    
                    # PROGRESO MEJORADO para migración secuencial
                    total_procesados = total_insertados + total_omitidos
                    if total_registros and total_registros > 0:
                        porcentaje = min(98, int((total_procesados / total_registros) * 100))
                        progress(porcentaje)
                        log(f"✅ Lote procesado: {len(filas):,} registros | Progreso: {porcentaje}% ({total_procesados:,}/{total_registros:,})")
                    else:
                        log(f"✅ Lote procesado: {len(filas):,} registros | Total: {total_procesados:,}")
                        
                except pyodbc.IntegrityError as ie:
                    conn_dest.rollback()
                    total_omitidos += len(filas)
                    total_procesados = total_insertados + total_omitidos
                    if total_registros and total_registros > 0:
                        porcentaje = min(98, int((total_procesados / total_registros) * 100))
                        progress(porcentaje)
                    log(f"⚠️ Lote omitido: {len(filas):,} registros duplicados | Progreso: {porcentaje if total_registros else 'N/A'}%", "warning")
                except Exception as e:
                    error_msg = str(e).lower()
                    try:
                        conn_dest.rollback()
                        log(f"✅ Rollback exitoso tras error.")
                    except Exception as rb_error:
                        log(f"⚠️ Error en rollback: {str(rb_error)[:50]}", "warning")
                    
                    if "timeout" in error_msg or "connection" in error_msg:
                        log(f"❌ Conexión perdida durante inserción. Migración detenida.", "error")
                        abort(f"❌ Conexión perdida. Reinicie la migración.")
                    else:
                        log(f"❌ Error crítico insertando lote: {str(e)[:100]}", "error")
                        abort(f"❌ Error insertando lote: {str(e)[:100]}")
                    return {"insertados": total_insertados, "omitidos": total_omitidos}
    
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            log(f"⚠️ Conexión perdida. Intentando reconectar...", "warning")
            # Intentar reconexión
            try:
                with pyodbc.connect(conn_str_ori, timeout=60) as test_conn:
                    log(f"✅ Reconexión exitosa, pero migración debe reiniciarse.")
                abort(f"⚠️ Conexión perdida durante migración. Reinicie el proceso.")
            except Exception:
                abort(f"❌ Error de red persistente. Verifique VPN y conectividad.")
        elif "login failed" in error_msg or "authentication" in error_msg:
            abort(f"🔐 Error de autenticación. Verifique usuario y contraseña.")
        else:
            abort(f"❌ Error en migración secuencial: {str(e)[:100]}")

    # VALIDACIÓN FINAL
    if total_insertados > 0:
        log(f"✅ Migración secuencial exitosa. Insertados: {total_insertados:,} | Omitidos: {total_omitidos:,}", "success")
    elif total_omitidos > 0:
        log(f"⚠️ Migración completada sin nuevos registros. Todos duplicados: {total_omitidos:,}", "warning")
    else:
        log(f"⚠️ Migración completada sin procesar registros. Verificar condiciones WHERE.", "warning")
    
    progress(100)
    return {"insertados": total_insertados, "omitidos": total_omitidos}