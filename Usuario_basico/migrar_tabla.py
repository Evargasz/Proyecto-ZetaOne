import sys, os
import pyodbc
import traceback
from collections import defaultdict
import re
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import logging
import json
import csv
from datetime import datetime
from decimal import Decimal

# --- IMPORTACIONES PARA PARALELIZACIÓN ---
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty

# --- CONFIGURACIÓN INICIAL ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
HISTORIAL_FILE = os.path.join("json", "historial_migraciones.json")

# --- FUNCIONES AUXILIARES ---

def guardar_en_historial(tipo_migracion, tabla, resultado, where=None, base_usuario=None, ajuste_columnas=None):
    """Guarda un registro de la migración en un archivo JSON (implementación mínima segura).

    Esta implementación evita accesos concurrentes complejos y asegura que el archivo
    `json/historial_migraciones.json` exista y contenga una lista de entradas.
    """
    try:
        entry = {
            'ts': datetime.utcnow().isoformat() + 'Z',
            'tipo': tipo_migracion,
            'tabla': tabla,
            'resultado': resultado,
            'where': where,
            'usuario': base_usuario,
            'ajuste_columnas': ajuste_columnas,
        }
        # Asegurar directorio
        hist_dir = os.path.dirname(HISTORIAL_FILE)
        if hist_dir and not os.path.exists(hist_dir):
            os.makedirs(hist_dir, exist_ok=True)

        # Leer existente (si hay) y anexar
        data = []
        try:
            with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        except Exception:
            data = []

        data.append(entry)
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # No fallar la aplicación por un error de historial.
        return


def consultar_tabla_e_indice(tabla, amb_origen, amb_destino, log, abort, where=None, base_usuario=None):
    """Verificación ligera entre origen y destino.

    - Recupera nombres de columnas (sin leer datos) de origen y destino.
    - Intenta obtener la clave primaria (consulta genérica a INFORMATION_SCHEMA cuando es posible).
    - Cuenta filas en origen (opcionalmente con `where`).
    - Registra un mensaje claro vía `log` indicando si las estructuras son compatibles o qué diferencias hay.

    Está pensada para ser rápida y segura en producción: captura excepciones y devuelve
    la estructura mínima que la UI necesita para habilitar el botón de migración.
    """
    def _build_conn_str_local(amb):
        drv = amb.get('driver', '')
        if 'Sybase' in drv:
            return f"DRIVER={{{drv}}};SERVER={amb.get('ip','')};PORT={amb.get('puerto','')};DATABASE={amb.get('base','')};UID={amb.get('usuario','')};PWD={amb.get('clave','')}"
        else:
            # Normalmente SQL Server u otros ODBC drivers
            return f"DRIVER={{{drv}}};SERVER={amb.get('ip','')},{amb.get('puerto','')};DATABASE={amb.get('base','')};UID={amb.get('usuario','')};PWD={amb.get('clave','')}"

    columnas_origen = []
    columnas_destino = []
    clave_primaria = []
    nregs = 0

    try:
        conn_str_ori = _build_conn_str_local(amb_origen)
        conn_str_dest = _build_conn_str_local(amb_destino)

        # Obtener columnas origen
        try:
            with pyodbc.connect(conn_str_ori, timeout=20) as conn_ori:
                cur = conn_ori.cursor()
                sql = f"SELECT * FROM {tabla} WHERE 1=0"
                cur.execute(sql)
                columnas_origen = [col[0] for col in cur.description]
        except Exception as e:
            log(f"⚠️ No se pudieron obtener columnas del origen: {str(e)[:200]}", "warning")

        # Obtener columnas destino
        try:
            with pyodbc.connect(conn_str_dest, timeout=20) as conn_dest:
                curd = conn_dest.cursor()
                sql = f"SELECT * FROM {tabla} WHERE 1=0"
                curd.execute(sql)
                columnas_destino = [col[0] for col in curd.description]
        except Exception as e:
            log(f"⚠️ No se pudieron obtener columnas del destino: {str(e)[:200]}", "warning")

        # Intentar obtener clave primaria desde INFORMATION_SCHEMA (SQL Server y compatibles)
        try:
            # Extraer nombre simple de tabla
            tbl_simple = tabla.split('.')[-1].strip()
            with pyodbc.connect(conn_str_dest, timeout=20) as conn_dest:
                curd = conn_dest.cursor()
                sql_pk = (
                    "SELECT k.COLUMN_NAME "
                    "FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t "
                    "JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME "
                    "WHERE t.TABLE_NAME = ? AND t.CONSTRAINT_TYPE = 'PRIMARY KEY'"
                )
                try:
                    curd.execute(sql_pk, tbl_simple)
                    clave_primaria = [row[0] for row in curd.fetchall()]
                except Exception:
                    clave_primaria = []
        except Exception:
            clave_primaria = []

        # Contar registros en origen
        try:
            with pyodbc.connect(conn_str_ori, timeout=30) as conn_ori:
                cur = conn_ori.cursor()
                sql_count = f"SELECT COUNT(*) FROM {tabla}"
                if where:
                    sql_count += f" WHERE {where}"
                cur.execute(sql_count)
                nregs = int(cur.fetchone()[0] or 0)
        except Exception:
            nregs = 0

        # Comparar estructuras (nombres en minúscula para evitar diferencias de case)
        cols_o = [c.lower() for c in columnas_origen]
        cols_d = [c.lower() for c in columnas_destino]

        compatible = cols_o == cols_d
        if compatible:
            log(f"✅ Estructura origen/destino compatible ({len(cols_o)} columnas).", "success")
        else:
            faltan = [c for c in cols_o if c not in cols_d]
            extras = [c for c in cols_d if c not in cols_o]
            msg = f"⚠️ Estructura distinta: origen={len(cols_o)} cols, destino={len(cols_d)} cols."
            if faltan:
                msg += f" | Faltan en destino: {faltan[:5]}{'...' if len(faltan)>5 else ''}"
            if extras:
                msg += f" | Extras en destino: {extras[:5]}{'...' if len(extras)>5 else ''}"
            log(msg, "warning")

        return {
            'columnas': columnas_origen,
            'clave_primaria': clave_primaria,
            'nregs': nregs,
            'ajuste_columnas': None,
            'columnas_destino': columnas_destino,
        }
    except Exception as e:
        log(f"❌ Error verificando estructura tabla: {str(e)[:200]}", "error")
        return {
            'columnas': columnas_origen,
            'clave_primaria': clave_primaria,
            'nregs': nregs,
            'ajuste_columnas': None,
            'columnas_destino': columnas_destino,
        }


def migrar_tabla(
    log_func=None, progress_func=None, abort_func=None,
    amb_origen=None, amb_destino=None, tabla=None, where=None, base_usuario=None,
    cancelar_func=None, total_registros=None, ajuste_columnas=None,
    columnas=None, columnas_destino=None, clave_primaria=None, **kwargs
):
    """Implementación completa y robusta de `migrar_tabla`.

    Características principales:
    - Obtiene metadatos (columnas, PK) si no se proporcionan.
    - Lee desde origen usando `fetchmany` por lotes.
    - Verifica duplicados en destino (cache parcial por lotes).
    - Sanitiza valores básicos (Decimal->float, strip strings, bytes->utf8).
    - Inserta por lotes con `executemany`, intentando usar `fast_executemany` si está disponible.
    - Realiza reintentos simples al hacer `commit` y reabre conexión si es necesario.
    """
    log = log_func or (lambda *a, **k: None)
    progress = progress_func or (lambda p: None)
    abort = abort_func or (lambda m: None)

    # Preparar carpeta de migración con timestamp en C:\ZetaOne\Migraciones
    try:
        migration_base = r"C:\ZetaOne\Migraciones"
        # Timestamp sin segundos: YYYYMMDDHHMM (el usuario pidió omitir segundos)
        migration_ts = datetime.utcnow().strftime('%Y%m%d%H%M')
        migration_root = os.path.join(migration_base, f"Migracion_{migration_ts}")
        rechazos_dir = os.path.join(migration_root, 'rechazos')
        os.makedirs(rechazos_dir, exist_ok=True)
        # Archivo único de duplicados para esta ejecución (incluye segundos)
        duplicados_file = os.path.join(rechazos_dir, f"duplicados_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt")
    except Exception:
        # Fallback a carpeta local si no se puede crear en C:\ZetaOne
        rechazos_dir = os.path.join('output', 'migration_rejects')
        os.makedirs(rechazos_dir, exist_ok=True)
        duplicados_file = os.path.join(rechazos_dir, f"duplicados_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt")

    def _build_conn_str_local(amb, autocommit=False):
        drv = amb.get('driver', '') if amb else ''
        if 'Sybase' in drv:
            return f"DRIVER={{{drv}}};SERVER={amb.get('ip','')};PORT={amb.get('puerto','')};DATABASE={amb.get('base','')};UID={amb.get('usuario','')};PWD={amb.get('clave','')}"
        else:
            return f"DRIVER={{{drv}}};SERVER={amb.get('ip','')},{amb.get('puerto','')};DATABASE={amb.get('base','')};UID={amb.get('usuario','')};PWD={amb.get('clave','')}"

    def _sanitizar_valor(v):
        try:
            if v is None:
                return None
            if isinstance(v, Decimal):
                return float(v)
            if isinstance(v, bytes):
                try:
                    return v.decode('utf-8')
                except Exception:
                    return v.decode('latin1', 'ignore')
            if isinstance(v, str):
                return v.strip()
            return v
        except Exception:
            return v

    def _format_update_sql(tabla_name, cols_all, pk_cols, row_values):
        """Construye una SQL UPDATE parametrizada y la lista de params.

        - `cols_all`: lista de columnas en el orden de `row_values`.
        - `pk_cols`: lista de columnas que componen la PK.
        """
        try:
            # Mapa col->valor
            row_map = {c: row_values[i] if i < len(row_values) else None for i, c in enumerate(cols_all)}
            set_cols = [c for c in cols_all if c not in pk_cols]
            set_clause = ','.join([f"{c}=?" for c in set_cols]) if set_cols else ''
            where_clause = ' AND '.join([f"{c}=?" for c in pk_cols]) if pk_cols else '1=1'
            sql = f"UPDATE {tabla_name} SET {set_clause} WHERE {where_clause}"
            params = [row_map.get(c) for c in set_cols] + [row_map.get(c) for c in pk_cols]
            return sql, params
        except Exception:
            return None, []

    def _write_audit_record(tabla_name, pk_names, pk_vals, row_map, db_message, suggested_sql, suggested_params):
        """Escribe un registro de auditoría en formato txt (JSON por línea + resumen .txt).

        - `rejected.txt`: cada línea contiene un JSON con el detalle completo.
        - `rejected_summary.txt`: archivo tipo CSV (separado por comas) con resumen por línea.
        """
        try:
            out_dir = rechazos_dir
            os.makedirs(out_dir, exist_ok=True)
            # Archivo principal: JSON por línea pero con extensión .txt según solicitud
            json_path = os.path.join(out_dir, 'rejected.txt')
            # Solo generar un archivo legible único por ejecución con timestamp que incluya
            # únicamente los registros duplicados en el formato solicitado.
            try:
                # Usar archivo único `duplicados_file` creado al inicio de la migración
                cols = list(row_map.keys())
                # Escribir en formato tabular: encabezado (columnas) una sola vez,
                # luego una línea por registro con los valores correspondientes.
                write_header = (not os.path.exists(duplicados_file)) or (os.path.getsize(duplicados_file) == 0)
                vals = [row_map.get(c) for c in cols]
                try:
                    with open(duplicados_file, 'a', encoding='utf-8') as df:
                        if write_header:
                            df.write('|'.join(cols) + '\n')
                        df.write('|'.join(json.dumps(v, ensure_ascii=False, default=str) for v in vals) + '\n')
                except Exception:
                    logging.getLogger(__name__).exception('No se pudo escribir archivo de duplicados')

                # Además escribir una copia local en workspace `output/migration_rejects` para facilitar revisión
                try:
                    local_dir = os.path.join('output', 'migration_rejects')
                    os.makedirs(local_dir, exist_ok=True)
                    local_dup = os.path.join(local_dir, os.path.basename(duplicados_file))
                    write_header_local = (not os.path.exists(local_dup)) or (os.path.getsize(local_dup) == 0)
                    with open(local_dup, 'a', encoding='utf-8') as ldf:
                        if write_header_local:
                            ldf.write('|'.join(cols) + '\n')
                        ldf.write('|'.join(json.dumps(v, ensure_ascii=False, default=str) for v in vals) + '\n')
                except Exception:
                    logging.getLogger(__name__).exception('No se pudo escribir copia local de duplicados')
            except Exception:
                logging.getLogger(__name__).exception('No se pudo escribir archivo de duplicados')
        except Exception:
            logging.getLogger(__name__).exception('No se pudo escribir registro de auditoría')

    def _manage_trigger(cursor, tabla_name, accion):
        # Implementación mínima: no-op o lógica DB específica si se quiere añadir.
        return

    def _commit_with_retries(conn, max_retries=3):
        backoff = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                conn.commit()
                return True, ''
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                msg = str(e)
                log(f"⚠️ Intento de commit {attempt} falló: {msg}", "warning")
                time.sleep(backoff)
                backoff *= 2
        return False, 'commit failed after retries'

    # Preparar información de tabla
    info = None
    # Solo ejecutar la verificación ligera si el llamador no proveyó la información necesaria
    try:
        # Si el llamador ya pasó las columnas y el total de registros, no es necesario
        # volver a ejecutar la verificación completa (evita mensajes duplicados en UI).
        need_info = (not columnas) or (total_registros is None)
        if need_info:
            info = consultar_tabla_e_indice(tabla, amb_origen, amb_destino, log, abort, where=where, base_usuario=base_usuario)
        else:
            info = {}
    except Exception as e:
        log(f"⚠️ No se pudo obtener info de tabla: {e}", "warning")

    columnas_origen = columnas or (info.get('columnas') if info else None)
    pk = clave_primaria or (info.get('clave_primaria') if info else [])
    nregs_estimado = total_registros or (info.get('nregs') if info else 0)

    if not columnas_origen:
        abort("No se pudo determinar columnas de origen.")
        return {"insertados": 0, "omitidos": 0}

    cols_insert = columnas_destino if columnas_destino else columnas_origen

    # Conexiones
    conn_str_ori = _build_conn_str_local(amb_origen)
    conn_str_dest = _build_conn_str_local(amb_destino)

    SUB_BATCH = 500
    COMMIT_BATCH = 1000

    insertados = 0
    omitidos = 0
    # Para evitar mensajes duplicados en la UI sobre la misma llave
    reported_duplicates = set()
    # Contador de duplicados por llave para resumen al final
    duplicate_counts = defaultdict(int)
    # Ejemplos por llave (hasta N) para mostrar en el resumen
    duplicate_examples = defaultdict(list)
    MAX_DUPLICATE_EXAMPLES = 10
    # Evitar escribir auditoría duplicada: almacenar hashes de filas ya auditadas
    audited_rows_hashes = set()
    def _make_key_repr(v):
        try:
            if v is None:
                return '<sin_llave>'
            return json.dumps(v, ensure_ascii=False, default=str, separators=(',', ':'))
        except Exception:
            try:
                return str(v)
            except Exception:
                return '<sin_llave>'

    conn_ori = None
    conn_dest = None
    try:
        conn_ori = pyodbc.connect(conn_str_ori, timeout=30)
        conn_dest = pyodbc.connect(conn_str_dest, timeout=30)
        cur_ori = conn_ori.cursor()
        cur_dest = conn_dest.cursor()

        # Intentar activar fast_executemany si existe
        try:
            cur_dest.fast_executemany = True
            fast_exec = getattr(cur_dest, 'fast_executemany', False)
        except Exception:
            fast_exec = False

        # Preparar select y recorrer por fetchmany
        sql_select = f"SELECT {','.join(columnas_origen)} FROM {tabla}"
        if where:
            sql_select += f" WHERE {where}"
        cur_ori.execute(sql_select)

        pending = []
        rows_fetched = 0
        while True:
            if cancelar_func and cancelar_func():
                log("⚠️ Migración cancelada por usuario.", "warning")
                break
            batch = cur_ori.fetchmany(SUB_BATCH)
            if not batch:
                break
            rows_fetched += len(batch)

            # Para cada fila, sanitizar y verificar duplicado por PK mediante consulta a destino
            pks_to_check = []
            sanitized_rows = []
            for row in batch:
                row_vals = [ _sanitizar_valor(v) for v in row ]
                sanitized_rows.append(tuple(row_vals))
                if pk:
                    if len(pk) == 1:
                        # Encontrar índice de pk
                        try:
                            idx = columnas_origen.index(pk[0])
                            pks_to_check.append(row_vals[idx])
                        except Exception:
                            pks_to_check.append(None)
                    else:
                        try:
                            idxs = [columnas_origen.index(k) for k in pk]
                            pks_to_check.append(tuple(row_vals[i] for i in idxs))
                        except Exception:
                            pks_to_check.append(None)
                else:
                    pks_to_check.append(None)

            # Verificar duplicados en destino
            to_insert_flags = [True] * len(sanitized_rows)
            if pk and any(p is not None for p in pks_to_check):
                # Single PK case: build IN (...) query to detect existing keys
                if len(pk) == 1:
                    vals = [p for p in pks_to_check if p is not None]
                    if vals:
                        placeholders = ','.join('?' for _ in vals)
                        sql_chk = f"SELECT {pk[0]} FROM {tabla} WHERE {pk[0]} IN ({placeholders})"
                        try:
                            cur_dest.execute(sql_chk, vals)
                            exist = set(r[0] for r in cur_dest.fetchall())
                            # Marcar los que ya existen
                            for i, p in enumerate(pks_to_check):
                                if p in exist:
                                    to_insert_flags[i] = False
                        except Exception:
                            pass
                else:
                    # Composite PK: check per row
                    for i, p in enumerate(pks_to_check):
                        if p is None:
                            continue
                        cond = ' AND '.join([f"{col}=?" for col in pk])
                        params = list(p)
                        sql_chk = f"SELECT 1 FROM {tabla} WHERE {cond}"
                        try:
                            cur_dest.execute(sql_chk, params)
                            if cur_dest.fetchone():
                                to_insert_flags[i] = False
                        except Exception:
                            pass

                # Informar al usuario por cada fila marcada como duplicada (valor usado para validación)
            try:
                for i, flag in enumerate(to_insert_flags):
                    if not flag:
                        val = pks_to_check[i]
                        if val is None:
                            # usar una muestra de la fila si no hay PK
                            preview = _make_key_repr(tuple(sanitized_rows[i][:3]))
                        else:
                            preview = _make_key_repr(val)
                        duplicate_counts[preview] += 1
                        # Guardar ejemplo (muestra) para el resumen final
                        try:
                            if len(duplicate_examples[preview]) < MAX_DUPLICATE_EXAMPLES:
                                # almacenar la representación breve (ya es una cadena JSON-like)
                                duplicate_examples[preview].append(preview)
                        except Exception:
                            pass
                            # No escribir auditoría aquí: solo contaremos ocurrencias y ejemplos.
                            pass
            except Exception:
                pass

            # Prepare batch to insert
            insert_batch = [r for flg, r in zip(to_insert_flags, sanitized_rows) if flg]
            omitidos += len(sanitized_rows) - len(insert_batch)

            if insert_batch:
                # Construir SQL insert
                cols = cols_insert
                sql_ins = f"INSERT INTO {tabla} ({','.join(cols)}) VALUES ({','.join(['?' for _ in cols])})"
                # Ajustar filas al orden de cols: si columnas_origen != cols, map
                if cols != columnas_origen:
                    mapped_rows = []
                    for r in insert_batch:
                        row_map = []
                        for c in cols:
                            try:
                                idx = columnas_origen.index(c)
                                row_map.append(r[idx])
                            except Exception:
                                row_map.append(None)
                        mapped_rows.append(tuple(row_map))
                    rows_to_exec = mapped_rows
                else:
                    rows_to_exec = insert_batch

                # Ejecutar en sub-lotes
                for j in range(0, len(rows_to_exec), COMMIT_BATCH):
                    sub = rows_to_exec[j:j+COMMIT_BATCH]
                    try:
                        cur_dest.executemany(sql_ins, sub)
                        success, msg = _commit_with_retries(conn_dest, max_retries=3)
                        if not success:
                            log(f"❌ Commit falló: {msg}", "error")
                            conn_dest.rollback()
                            # En caso de fallo, no intentar más con este sublote
                            continue
                        insertados += len(sub)
                        try:
                            progreso = int(min(100, (rows_fetched / max(1, nregs_estimado)) * 100))
                            progress(progreso)
                        except Exception:
                            pass
                    except Exception as e:
                        err_msg = str(e)
                        # Mostrar mensaje claro para usuario si es error de duplicado
                        if 'duplicate' in err_msg.lower() or 'duplicate key' in err_msg.lower() or '2601' in err_msg:
                            try:
                                sample_pk = None
                                # intentar extraer PK de la primera fila del sublote
                                first = sub[0]
                                if pk:
                                    if len(pk) == 1 and pk[0] in cols:
                                        idxpk = cols.index(pk[0])
                                        sample_pk = first[idxpk]
                                    else:
                                        idxs = [cols.index(k) for k in pk if k in cols]
                                        sample_pk = tuple(first[i] for i in idxs)
                                # Construir representación legible de la PK duplicada
                                pk_names = list(pk) if pk else []
                                key_repr = _make_key_repr(sample_pk)
                                # Preparar valor de validación (muestra breve de la fila si no hay PK)
                                try:
                                    if sample_pk is not None:
                                        preview_val = _make_key_repr(sample_pk)
                                    else:
                                        preview_val = _make_key_repr(tuple(first[:3]))
                                except Exception:
                                    preview_val = '<sin_valor>'
                                # No mostrar mensaje UI aquí (se notifican en la verificación previa por registro).
                                # Registrar detalle técnico para debugging y crear auditoría.
                                logging.getLogger(__name__).debug(f"DB duplicate error (batch): {err_msg} | ejemplo_valor_pk: {sample_pk}")
                                # Batch duplicate detected: no escribir auditoría aquí. Se intentará
                                # insertar fila-a-fila a continuación y la auditoría se generará
                                # únicamente para aquellas filas que realmente fallen por duplicado.
                                logging.getLogger(__name__).debug('Batch duplicate detected; delegando auditoría a inserción por fila')
                            except Exception:
                                pk_names = list(pk) if pk else []
                                key_repr = _make_key_repr(None)
                                try:
                                    preview_val = _make_key_repr(tuple(first[:3]))
                                except Exception:
                                    preview_val = '<sin_valor>'
                                logging.getLogger(__name__).debug(f"DB duplicate error (batch, no sample pk): {err_msg}")
                                logging.getLogger(__name__).debug('Batch duplicate detected (no sample pk); delegando auditoría a inserción por fila')
                        else:
                            log(f"❌ Error insertando lote: {err_msg[:300]}", "error")
                        try:
                            conn_dest.rollback()
                        except Exception:
                            pass
                        # intentar insertar fila a fila para recolectar errores
                        for row_err in sub:
                            try:
                                cur_dest.execute(sql_ins, row_err)
                                conn_dest.commit()
                                insertados += 1
                            except Exception as e2:
                                emsg = str(e2)
                                # Detectar duplicado y extraer PK para mensaje amigable
                                is_dup = ('duplicate' in emsg.lower() or 'duplicate key' in emsg.lower() or '2601' in emsg)
                                pk_vals = None
                                try:
                                    if pk:
                                        if len(pk) == 1 and pk[0] in cols:
                                            idxpk = cols.index(pk[0])
                                            pk_vals = row_err[idxpk]
                                        else:
                                            idxs = [cols.index(k) for k in pk if k in cols]
                                            pk_vals = tuple(row_err[i] for i in idxs)
                                except Exception:
                                    pk_vals = None

                                if is_dup:
                                    pk_names = list(pk) if pk else []
                                    key_repr = _make_key_repr(pk_vals)
                                    try:
                                        if pk_vals is not None:
                                            preview_val = _make_key_repr(pk_vals)
                                        else:
                                            preview_val = _make_key_repr(tuple(row_err[:3]))
                                    except Exception:
                                        preview_val = '<sin_valor>'
                                    # Contar duplicado y guardar ejemplo para resumen; no log UI repetitivo
                                    duplicate_counts[key_repr] += 1
                                    try:
                                        if len(duplicate_examples[key_repr]) < MAX_DUPLICATE_EXAMPLES:
                                            duplicate_examples[key_repr].append(preview_val)
                                    except Exception:
                                        pass
                                    logging.getLogger(__name__).debug(f"Registro rechazado por duplicado. PK_valor={pk_vals}. Mensaje DB: {emsg}")
                                    try:
                                        # Construir row_map para auditoría
                                        row_map = {c: row_err[i] if i < len(row_err) else None for i, c in enumerate(cols)}
                                        suggested_sql, suggested_params = _format_update_sql(tabla, cols, pk, row_err)
                                        try:
                                            row_hash = json.dumps([row_map.get(c) for c in cols], ensure_ascii=False, default=str)
                                        except Exception:
                                            row_hash = None
                                        if not row_hash or row_hash not in audited_rows_hashes:
                                            if row_hash:
                                                audited_rows_hashes.add(row_hash)
                                            _write_audit_record(tabla, pk_names, pk_vals, row_map, emsg, suggested_sql, suggested_params)
                                    except Exception:
                                        logging.getLogger(__name__).exception('Error escribiendo auditoría por registro duplicado')
                                else:
                                    log(f"⚠️ Registro rechazado: {emsg[:200]}", "warning")
                                try:
                                    conn_dest.rollback()
                                except Exception:
                                    pass

        # Fin while

        # Emitir resumen de duplicados detectados (una línea por llave)
        try:
            for key_repr, cnt in duplicate_counts.items():
                # Mostrar el valor usado para validación, cuántas ocurrencias y hasta N ejemplos
                examples = duplicate_examples.get(key_repr, [])
                try:
                    ex_disp = json.dumps(examples, ensure_ascii=False, default=str)
                except Exception:
                    ex_disp = str(examples)
                log(f"⚠️ Registro(s) rechazado(s) por duplicado. Llave: {key_repr} | ocurrencias: {cnt} | ejemplos: {ex_disp}", "warning")
        except Exception:
            pass

        log(f"🏁 Hilo terminado. Insertados: {insertados:,}, Omitidos: {omitidos:,}")
        return {"insertados": insertados, "omitidos": omitidos}

    except Exception as e:
        log(f"❌ Error crítico en migración: {str(e)[:300]}", "error")
        try:
            if conn_dest:
                conn_dest.rollback()
        except Exception:
            pass
        abort(f"Error en migración: {str(e)}")
        return {"insertados": insertados, "omitidos": omitidos}

    finally:
        try:
            if conn_ori:
                conn_ori.close()
        except Exception:
            pass
        try:
            if conn_dest:
                conn_dest.close()
        except Exception:
            pass
    