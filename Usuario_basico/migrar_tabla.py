import pyodbc
import traceback
import tkinter as tk
from tkinter import messagebox
import threading

# ==================== LOGICA DE BACKEND MIGRACION ====================

def _build_conn_str(amb):
    driver = amb['driver']
    if driver == 'Sybase ASE ODBC Driver':
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={amb['ip']};"
            f"PORT={amb['puerto']};"
            f"DATABASE={amb['base']};"
            f"UID={amb['usuario']};"
            f"PWD={amb['clave']};"
        )
    else:
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={amb['ip']},{amb['puerto']};"
            f"DATABASE={amb['base']};"
            f"UID={amb['usuario']};"
            f"PWD={amb['clave']};"
        )

def columnas_tabla(conn_str, tabla):
    with pyodbc.connect(conn_str, timeout=8) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {tabla} WHERE 1=0")
            return [desc[0] for desc in cur.description]

def pk_tabla(conn_str, tabla, is_sybase):
    import re
    with pyodbc.connect(conn_str, timeout=8, autocommit=True) as conn:
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
                else:
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
                    if not pk_cols:
                        consulta_unique = """
                        SELECT col.name
                        FROM sys.indexes idx
                        INNER JOIN sys.index_columns ic ON idx.object_id = ic.object_id AND idx.index_id = ic.index_id
                        INNER JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
                        INNER JOIN sys.tables t ON idx.object_id = t.object_id
                        WHERE idx.is_unique = 1 AND t.name = ?
                        ORDER BY idx.name, ic.key_ordinal
                        """
                        cur.execute(consulta_unique, (nombre_tb_simple,))
                        res = cur.fetchall()
                        if res:
                            pk_cols = [row[0].lower() for row in res]
            except Exception:
                pk_cols = []
            return pk_cols

def consultar_tabla_e_indice(tabla, amb_origen, amb_destino, log_func, abort_func, where=None, base_usuario=None):
    is_sybase = amb_destino["driver"].lower().startswith("sybase")
    tabla_simple = tabla.split('.')[-1]
    tabla_ref = tabla_simple
    amb_origen_db = amb_origen.copy()
    amb_destino_db = amb_destino.copy()
    if base_usuario:
        amb_origen_db['base'] = base_usuario
        amb_destino_db['base'] = base_usuario
    conn_str_ori = _build_conn_str(amb_origen_db)
    conn_str_dest = _build_conn_str(amb_destino_db)
    try:
        cols_ori = columnas_tabla(conn_str_ori, tabla_ref)
        cols_dest = columnas_tabla(conn_str_dest, tabla_ref)
    except Exception as e:
        abort_func(f"Error consultando columnas: {e}")
        return None
    if cols_ori != cols_dest:
        abort_func(f"Estructura diferente entre origen y destino. Origen: {cols_ori}, Destino: {cols_dest}")
        return None
    else:
        log_func(f"✅ La estructura de la tabla es igual en origen y destino. Puedes continuar con la migración.")
    try:
        pk = pk_tabla(conn_str_ori, tabla_simple, is_sybase)
    except Exception as e:
        pk = []
        log_func(f"[{tabla_simple}] Error buscando clave primaria: {e}")
    try:
        with pyodbc.connect(conn_str_ori, timeout=8) as conn:
            with conn.cursor() as cur:
                sql = f"SELECT COUNT(*) FROM {tabla_ref}"
                if where:
                    sql += f" WHERE {where}"
                cur.execute(sql)
                nregs = cur.fetchone()[0]
    except Exception as e:
        nregs = -1
        log_func(f"Ocurrió un error contando registros: {e}")
    return {
        "columnas": cols_ori,
        "clave_primaria": pk,
        "nregs": nregs,
    }

def migrar_tabla(
    tabla,
    where,
    amb_origen, amb_destino,
    log_func=None,
    progress_func=None,
    abort_func=None,
    columnas=None,
    clave_primaria=None,
    base_usuario=None,
    cancelar_func=None
):
    import pyodbc
    import traceback

    print("------ INICIO DE FUNCIÓN MIGRAR_TABLA ------")
    log = log_func if log_func else print
    progress = progress_func if progress_func else lambda x: None
    abort = abort_func if abort_func else lambda msg: print(f"ABORT: {msg}")
    is_sybase = amb_destino['driver'].lower().startswith("sybase")
    tabla_simple = tabla.split('.')[-1]
    columnas_ori = columnas
    pk_cols = clave_primaria

    if not columnas_ori or pk_cols is None:
        conn_str_ori = _build_conn_str(amb_origen)
        columnas_ori = columnas_ori or columnas_tabla(conn_str_ori, tabla_simple)
        pk_cols = pk_cols or pk_tabla(conn_str_ori, tabla_simple, is_sybase)

    if base_usuario:
        amb_origen = amb_origen.copy()
        amb_destino = amb_destino.copy()
        amb_origen['base'] = base_usuario
        amb_destino['base'] = base_usuario

    conn_str_ori = _build_conn_str(amb_origen)
    conn_str_dest = _build_conn_str(amb_destino)

    # Chequeo rápido de cancelación
    if cancelar_func and cancelar_func():
        abort(f"[{tabla_simple}] Migración cancelada por el usuario (antes de procesar columnas).")
        return {"insertados": 0, "omitidos": 0}

    try:
        columnas_dest = columnas_tabla(conn_str_dest, tabla_simple)
        if columnas_ori != columnas_dest:
            abort(f"Estructura diferente entre origen y destino en '{tabla_simple}'. Origen: {columnas_ori}, Destino: {columnas_dest}")
            return {"insertados": 0, "omitidos": 0}
    except Exception as e:
        abort(f"Error consultando columnas: {e}")
        return {"insertados": 0, "omitidos": 0}

    log(f"[{tabla_simple}] Llave primaria (o índice unique) detectada: {pk_cols}" if pk_cols else f"[{tabla_simple}] ¡ATENCIÓN! No se detectó PK/índice unique. Puede haber duplicados.")

    # Chequeo rápido de cancelación
    if cancelar_func and cancelar_func():
        abort(f"[{tabla_simple}] Migración cancelada por el usuario (tras verificación de columnas).")
        return {"insertados": 0, "omitidos": 0}

    try:
        print("------ LEYENDO PKS DEL DESTINO ------")
        print(f"[DEBUG migrar_tabla] pk_cols para destino: {pk_cols}")
        with pyodbc.connect(conn_str_dest, timeout=8) as conn_dest:
            with conn_dest.cursor() as cur_dest:
                if pk_cols and all(pk_cols):
                    query = f"SELECT {','.join(pk_cols)} FROM {tabla_simple}"
                    if where:
                        query += f" WHERE {where}"
                    print(f"[DEBUG migrar_tabla] Query para obtener PKs destino: {query}")
                    cur_dest.execute(query)
                    pks_dest = set(tuple(row) for row in cur_dest.fetchall())
                    print(f"------ PKS EN DESTINO: {pks_dest} ------")
                else:
                    raise Exception("No se detectó clave primaria ni índice UNIQUE en la tabla destino")
    except Exception as e:
        print(f"[DEBUG migrar_tabla] Excepción detallada: {e}")
        traceback.print_exc()
        abort(f"[{tabla_simple}] Error obteniendo PKs actuales en destino: {e}")
        return {"insertados": 0, "omitidos": 0}

    # Chequeo después de proceso pesado de PK
    if cancelar_func and cancelar_func():
        abort(f"[{tabla_simple}] Migración cancelada por el usuario (tras PK).")
        return {"insertados": 0, "omitidos": 0}

    try:
        print("------ LEYENDO FILAS DE ORIGEN ------")
        with pyodbc.connect(conn_str_ori, timeout=8) as conn_ori:
            with conn_ori.cursor() as cur_ori:
                cols_list = ','.join(columnas_ori)
                sql = f"SELECT {cols_list} FROM {tabla_simple}"
                if where:
                    sql += f" WHERE {where}"
                progress(30)
                cur_ori.execute(sql)
                filas = cur_ori.fetchall()
                colnames = [d[0] for d in cur_ori.description]
                print(f"------ FILAS ORIGEN TRAIDAS: {len(filas)} ------")
    except Exception as e:
        abort(f"[{tabla_simple}] Error leyendo datos origen: {e}")
        return {"insertados": 0, "omitidos": 0}

    # Chequeo después de traer todos los datos
    if cancelar_func and cancelar_func():
        abort(f"[{tabla_simple}] Migración cancelada por el usuario (tras fetch de datos).")
        return {"insertados": 0, "omitidos": 0}

    try:
        with pyodbc.connect(conn_str_dest, timeout=8) as conn_dest:
            with conn_dest.cursor() as cur_dest:
                cur_dest.execute(f"SELECT COUNT(*) FROM {tabla_simple}")
                cuantos_destino = cur_dest.fetchone()[0]
    except Exception:
        cuantos_destino = 0

    if cuantos_destino == 0:
        log(f"[{tabla_simple}] Tabla destino VACÍA. Se insertarán TODOS los registros del origen en un único lote y commit.")
        insertables = [[getattr(row, col) for col in columnas_ori] for row in filas]
        omitidos = 0
        if not insertables:
            log(f"[{tabla_simple}] No hay registros para insertar (tabla origen vacía).")
            progress(100)
            return {"insertados": 0, "omitidos": 0}

        # Chequeo antes de la única inserción masiva
        if cancelar_func and cancelar_func():
            abort(f"[{tabla_simple}] Migración cancelada por el usuario (antes de insertar todo el lote).")
            return {"insertados": 0, "omitidos": 0}

        try:
            with pyodbc.connect(conn_str_dest, timeout=8) as conn_dest:
                with conn_dest.cursor() as cur_dest:
                    sqlin = f"INSERT INTO {tabla_simple} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})"
                    progress(60)
                    cur_dest.executemany(sqlin, insertables)
                    conn_dest.commit()
            log(f"[{tabla_simple}] Migración FINALIZADA (tabla destino vacía). Insertados: {len(insertables)}")
            progress(100)
            return {"insertados": len(insertables), "omitidos": 0}
        except Exception as e:
            abort(f"[{tabla_simple}] Error global insertando: {e}")
            return {"insertados": 0, "omitidos": 0}

    progress(40)
    insertables = []
    omitidos = 0
    print("------ INICIO DE EVALUACION DE CLAVES ORIGEN VS DESTINO ------")
    if pk_cols:
        for row in filas:
            # Chequeo frecuente durante grandes ciclos también es posible aquí si filas>> grandes
            if cancelar_func and cancelar_func():
                abort(f"[{tabla_simple}] Migración cancelada por el usuario (durante evaluación de duplicados).")
                return {"insertados": 0, "omitidos": omitidos}

            key = tuple(getattr(row, col) for col in pk_cols)
            if key not in pks_dest:
                insertables.append([getattr(row, col) for col in columnas_ori])
            else:
                omitidos += 1
    else:
        insertables = [[getattr(row, col) for col in columnas_ori] for row in filas]

    total_insertados = 0
    if not insertables:
        log(f"[{tabla_simple}] No hay registros para insertar (todo duplicado o vacía tabla origen).")
        log(f"Total insertados: 0, Total omitidos {omitidos}")
        progress(100)
        return {"insertados": 0, "omitidos": omitidos}

    progress(50)
    try:
        with pyodbc.connect(conn_str_dest, timeout=8) as conn_dest:
            with conn_dest.cursor() as cur_dest:
                conn_dest.autocommit = False
                # Puedes reducir el lote a 1000 para hacer aún más responsiva la cancelación
                lotes = 3000
                total = len(insertables)
                for i in range(0, total, lotes):
                    # Chequeo de cancelación antes de cada batch
                    if cancelar_func and cancelar_func():
                        conn_dest.rollback()
                        abort(f"[{tabla_simple}] cancelado por el usuario. Todas las inserciones fueron deshechas")
                        log(f"[{tabla_simple}] Migracion cancelada por el usuario. Revirtiendo cambios.")
                        return {"insertados": total_insertados, "omitidos": omitidos}

                    batch = insertables[i:i + lotes]
                    try:
                        sqlin = f"INSERT INTO {tabla_simple} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})"
                        cur_dest.executemany(sqlin, batch)
                        conn_dest.commit()
                        total_insertados += len(batch)
                        percent = 50 + int(50 * min(i + lotes, total) / total)
                        progress(percent)
                    except Exception as e:
                        conn_dest.rollback()
                        log(f"[{tabla_simple}] Error insertando lote {i//lotes+1}: {e}")
    except Exception as e:
        abort(f"[{tabla_simple}] Error global insertando: {e}")
        return {"insertados": 0, "omitidos": omitidos}

    log(f"[{tabla_simple}] Migración finalizada. Insertados: {total_insertados}, Omitidos por duplicado: {omitidos}")
    progress(100)
    return {"insertados": total_insertados, "omitidos": omitidos}