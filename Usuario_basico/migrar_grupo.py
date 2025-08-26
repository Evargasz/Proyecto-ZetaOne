import pyodbc
import re

def columnas_tabla(conn_str, tabla):
    """
    Obtiene la lista de columnas reales (respeta mayúsculas/minúsculas)
    """
    conn = pyodbc.connect(conn_str, timeout=8)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {tabla} WHERE 1=0")
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return cols

def pk_tabla(conn_str, tabla, is_sybase):
    import re
    conn = pyodbc.connect(conn_str, timeout=8, autocommit=True)
    cur = conn.cursor()
    pk_cols = []
    partes = tabla.split('.')
    nombre_tb_simple = partes[-1]

    try:
        if is_sybase:
            try:
                cur.execute("sp_pkeys @table_name=?", [nombre_tb_simple])
                pk_cols = [row.column_name.lower().strip() for row in cur.fetchall()]
            except Exception as e:
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
                except Exception as e:
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
    finally:
        cur.close()
        conn.close()
    return pk_cols

def migrar_grupo(grupo_conf, variables, amb_origen, amb_destino, log_func, progress_func, abort_func):
    """
    Migra un grupo de tablas relacionadas, respetando estructura y control de duplicados.
    """
    log = log_func if log_func else print
    progress = progress_func if progress_func else lambda x: None
    abort = abort_func if abort_func else lambda msg: print(f"ABORT: {msg}")

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

    conn_str_ori = _build_conn_str(amb_origen)
    conn_str_dest = _build_conn_str(amb_destino)
    tablas = grupo_conf['tablas']
    batch_size = 2000
    total_global = 0
    total_tablas = len(tablas)

    for idx_tabla, tabla_conf in enumerate(tablas):
        tabla = tabla_conf['tabla']
        llave = tabla_conf.get('llave', "")
        join = tabla_conf.get('join', "")
        condicion = tabla_conf.get('condicion', "")
        where = condicion
        for var, val in variables.items():
            where = where.replace(f"${var}$", val)

        # 1. Validar estructura
        try:
            cols_ori = columnas_tabla(conn_str_ori, tabla)
            cols_dest = columnas_tabla(conn_str_dest, tabla)
        except Exception as e:
            abort(f"[{tabla}] Error consultando columnas: {e}")
            return
        if cols_ori != cols_dest:
            abort(f"[{tabla}] Estructura diferente. Origen: {cols_ori} / Destino: {cols_dest}")
            continue
        else:
            log(f"[{tabla}] ✅ Estructura igual en origen y destino.")

        # 2. Detectar PK o índice unique
        pk_cols = []
        try:
            pk_cols = pk_tabla(conn_str_ori, tabla, True)  # True=Sybase
        except Exception as e:
            log(f"[{tabla}] Advertencia: Error detectando PK: {e}")
            pk_cols = []

        log(f"[{tabla}] PK/índice unique detectado: {pk_cols}" if pk_cols else f"[{tabla}] ¡ATENCIÓN! No se detectó PK/índice unique. Puede haber duplicados.")

        # 3. Armar SQL extracción
        if llave and join:
            sql = f"SELECT tbl.* FROM {tabla} tbl JOIN {llave} pri ON {join}"
            if where:
                sql += f" WHERE {where}"
        else:
            sql = f"SELECT * FROM {tabla}"
            if where:
                sql += f" WHERE {where}"
        log(f"[{tabla}] SQL de extracción: {sql}")

        # 4. Leer registros del origen
        try:
            conn_ori = pyodbc.connect(conn_str_ori, timeout=8)
            cur_ori = conn_ori.cursor()
            cur_ori.execute(sql)
            filas = cur_ori.fetchall()
            colnames = [d[0] for d in cur_ori.description]
            log(f"[{tabla}] Leídos del origen: {len(filas)}")
            cur_ori.close()
            conn_ori.close()
        except Exception as e:
            abort(f"[{tabla}] Error leyendo datos origen: {e}")
            return

        # 5. Leer PKs destino si corresponde (para evitar duplicados)
        pks_dest = set()
        if pk_cols:
            try:
                conn_dest = pyodbc.connect(conn_str_dest, timeout=8)
                cur_dest = conn_dest.cursor()
                cur_dest.execute(f"SELECT {','.join(pk_cols)} FROM {tabla}")
                pks_dest = set(tuple(row) for row in cur_dest.fetchall())
                cur_dest.close()
                conn_dest.close()
            except Exception as e:
                log(f"[{tabla}] Error obteniendo PKs en destino: {e}")
                pks_dest = set()
        log(f"[{tabla}] Total PKs en destino: {len(pks_dest)}")

        # 6. Preparar insertables y omitidos
        insertables = []
        omitidos = 0
        if pk_cols:
            for row in filas:
                key = tuple(getattr(row, col) for col in pk_cols)
                if key not in pks_dest:
                    insertables.append([getattr(row, col) for col in colnames])
                else:
                    omitidos += 1
        else:
            insertables = [[getattr(row, col) for col in colnames] for row in filas]

        log(f"[{tabla}] Insertables: {len(insertables)} / Omitidos (duplicados): {omitidos}")

        # 7. Insertar en destino
        migrados = 0
        if insertables:
            try:
                conn_dest = pyodbc.connect(conn_str_dest, timeout=8)
                cur_dest = conn_dest.cursor()
                conn_dest.autocommit = False
                for i in range(0, len(insertables), batch_size):
                    batch = insertables[i:i+batch_size]
                    try:
                        cur_dest.executemany(
                            f"INSERT INTO {tabla} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})",
                            batch
                        )
                        migrados += len(batch)
                        percent_tabla = int(100 * (idx_tabla + migrados/max(1,len(insertables))) / total_tablas)
                        progress(percent_tabla)
                    except Exception as e:
                        log(f"[{tabla}] Error insertando lote: {e}")
                        continue
                conn_dest.commit()
                log(f"[{tabla}] {migrados} registros migrados correctamente.")
                cur_dest.close()
                conn_dest.close()
            except Exception as e:
                abort(f"[{tabla}] Error global al insertar en destino: {e}")
                return
        else:
            log(f"[{tabla}] No hay registros para insertar.")

        total_global += migrados
        progress(int(100 * (idx_tabla+1) / total_tablas))

    log(f"✅ Migración de grupo finalizada. Total migrados: {total_global}")