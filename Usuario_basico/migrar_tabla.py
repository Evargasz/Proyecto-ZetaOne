import pyodbc

def _build_conn_str(amb):
    driver = amb['driver']
    # Sybase: ; en el host, SQL Server: , en el host
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
    """
    Obtiene la lista de columnas reales de la tabla usando su nombre simple u owner.tabla
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
    # Nos quedamos solo con el nombre simple de la tabla para Sybase
    nombre_tb_simple = partes[-1]

    print(f"[DEBUG pk_tabla] tabla: {tabla}, nombre_tb_simple: {nombre_tb_simple}, is_sybase: {is_sybase}")
    try:
        if is_sybase:
            try:
                cur.execute("sp_pkeys @table_name=?", [nombre_tb_simple])
                pk_cols = [row.column_name.lower().strip() for row in cur.fetchall()]
                print(f"[DEBUG pk_tabla] PK columns from sp_pkeys: {pk_cols}")
            except Exception as e:
                print(f"[DEBUG pk_tabla] sp_pkeys failed: {e}")
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
                            print(f"[DEBUG pk_tabla] Analizando indices 'unique'...")
                            for row in rows:
                                print(f"[DEBUG pk_tabla] index_description: {row[idx_desc_idx]}, index_keys: {row[idx_keys_idx]}")
                                idx_desc = row[idx_desc_idx]
                                if re.search(r'\bunique\b', idx_desc, re.IGNORECASE):
                                    print(f"[DEBUG pk_tabla] ¡Encontrado índice unique!: {idx_desc}")
                                    pk_cols = [col.strip() for col in row[idx_keys_idx].strip().split(',')]
                                    print(f"[DEBUG pk_tabla] Columnas del índice unique: {pk_cols}")
                                    found = True
                                    break
                            if found:
                                break
                        if not cur.nextset():
                            break
                except Exception as e:
                    print(f"[DEBUG pk_tabla] sp_help failed: {e}")
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
            print(f"[DEBUG pk_tabla] PK columns from MSSQL: {pk_cols}")
    finally:
        cur.close()
        conn.close()
    print(f"[DEBUG pk_tabla] Valor final a devolver: {pk_cols}")
    return pk_cols

def probar_conexion(conn_str, ambiente, log_func, abort_func):
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        conn.close()
        log_func(f"✅ Conexión exitosa con el ambiente '{ambiente['nombre']}' [Base: '{ambiente['base']}'].")
        return True
    except Exception as e:
        abort_func(
            f"❌ Error de CONEXIÓN al ambiente '{ambiente['nombre']}' [Base: '{ambiente['base']}'].\n"
            f"Revise usuario, contraseña, red, puerto, servidor o base seleccionada.\n"
            f"Detalle técnico: {e}"
        )
        return False

def consultar_tabla_e_indice(tabla, amb_origen, amb_destino, log_func, abort_func, where=None, base_usuario=None):
    """
    Consulta las columnas y clave primaria de una tabla en el origen y valida que existe en destino también.
    Devuelve: {"columnas": [...], "clave_primaria": [...], "nregs": ...}
    Para Sybase: usa solo el nombre simple de la tabla y asegurando conexión directa a la base dada.
    """
    is_sybase = amb_destino["driver"].lower().startswith("sybase")
    # Trabajamos solo con el nombre simple de la tabla
    tabla_simple = tabla.split('.')[-1]
    tabla_ref = tabla_simple  # para Sybase

    # Prepara ambientes con la base correcta
    amb_origen_db = amb_origen.copy()
    amb_destino_db = amb_destino.copy()
    if base_usuario:
        amb_origen_db['base'] = base_usuario
        amb_destino_db['base'] = base_usuario
    conn_str_ori = _build_conn_str(amb_origen_db)
    conn_str_dest = _build_conn_str(amb_destino_db)

    # ---- Prueba de conexión antes de seguir ----
    if not probar_conexion(conn_str_ori, amb_origen_db, log_func, abort_func):
        return None
    if not probar_conexion(conn_str_dest, amb_destino_db, log_func, abort_func):
        return None

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

    # -- LOG PARA AUDITORÍA --
    log_func(f"(DEBUG) Consultando índices/llaves en base='{amb_origen_db['base']}', tabla='{tabla_simple}', Sybase={is_sybase}")

    # Detecta clave primaria o índice único
    try:
        pk = pk_tabla(conn_str_ori, tabla_simple, is_sybase)
    except Exception as e:
        pk = []
        log_func(f"[{tabla_simple}] Error buscando clave primaria: {e}")

    # Cuenta registros
    try:
        conn = pyodbc.connect(conn_str_ori, timeout=8)
        cur = conn.cursor()
        sql = f"SELECT COUNT(*) FROM {tabla_ref}"
        if where:
            sql += f" WHERE {where}"
        cur.execute(sql)
        nregs = cur.fetchone()[0]
        cur.close()
        conn.close()
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
    base_usuario=None
):
    import pyodbc

    log = log_func if log_func else print
    progress = progress_func if progress_func else lambda x: None
    abort = abort_func if abort_func else lambda msg: print(f"ABORT: {msg}")

    is_sybase = amb_destino['driver'].lower().startswith("sybase")
    # Siempre usar solo el nombre simple de la tabla
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

    try:
        columnas_dest = columnas_tabla(conn_str_dest, tabla_simple)
        if columnas_ori != columnas_dest:
            abort(f"Estructura diferente entre origen y destino en '{tabla_simple}'. Origen: {columnas_ori}, Destino: {columnas_dest}")
            return {"insertados": 0, "omitidos": 0}
    except Exception as e:
        abort(f"Error consultando columnas: {e}")
        return {"insertados": 0, "omitidos": 0}

    log(f"[{tabla_simple}] Llave primaria (o índice unique) detectada: {pk_cols}" if pk_cols else f"[{tabla_simple}] ¡ATENCIÓN! No se detectó PK/índice unique. Puede haber duplicados.")

    try:
        # Consultar si la tabla destino está vacía
        conn_dest = pyodbc.connect(conn_str_dest, timeout=8)
        cur_dest = conn_dest.cursor()
        cur_dest.execute(f"SELECT COUNT(*) FROM {tabla_simple}")
        cuantos_destino = cur_dest.fetchone()[0]
        cur_dest.close()
        conn_dest.close()
        progress(20)
    except Exception as e:
        abort(f"[{tabla_simple}] Error consultando cantidad de registros en destino: {e}")
        return {"insertados": 0, "omitidos": 0}

    # Leer datos del origen según WHERE (si aplica)
    try:
        conn_ori = pyodbc.connect(conn_str_ori, timeout=8)
        cur_ori = conn_ori.cursor()
        cols_list = ','.join(columnas_ori)
        sql = f"SELECT {cols_list} FROM {tabla_simple}"
        if where:
            sql += f" WHERE {where}"
        progress(30)
        cur_ori.execute(sql)
        filas = cur_ori.fetchall()
        colnames = [d[0] for d in cur_ori.description]
        cur_ori.close()
        conn_ori.close()
    except Exception as e:
        abort(f"[{tabla_simple}] Error leyendo datos origen: {e}")
        return {"insertados": 0, "omitidos": 0}

    if cuantos_destino == 0:
        log(f"[{tabla_simple}] Tabla destino VACÍA. Se insertarán TODOS los registros del origen en un único lote y commit.")
        insertables = [[getattr(row, col) for col in columnas_ori] for row in filas]
        omitidos = 0

        if not insertables:
            log(f"[{tabla_simple}] No hay registros para insertar (tabla origen vacía).")
            progress(100)
            return {"insertados": 0, "omitidos": 0}

        try:
            conn_dest = pyodbc.connect(conn_str_dest, timeout=8)
            cur_dest = conn_dest.cursor()
            sqlin = f"INSERT INTO {tabla_simple} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})"
            progress(60)
            cur_dest.executemany(sqlin, insertables)
            conn_dest.commit()
            cur_dest.close()
            conn_dest.close()
            log(f"[{tabla_simple}] Migración FINALIZADA (tabla destino vacía). Insertados: {len(insertables)}")
            progress(100)
            return {"insertados": len(insertables), "omitidos": 0}
        except Exception as e:
            abort(f"[{tabla_simple}] Error global insertando: {e}")
            return {"insertados": 0, "omitidos": 0}

    # Para el caso cuando la tabla destino TIENE datos (incremental)
    progress(40)
    try:
        conn_dest = pyodbc.connect(conn_str_dest, timeout=8)
        cur_dest = conn_dest.cursor()
        if pk_cols:
            cur_dest.execute(f"SELECT {','.join(pk_cols)} FROM {tabla_simple}")
            pks_dest = set(tuple(row) for row in cur_dest.fetchall())
        else:
            pks_dest = set()
        cur_dest.close()
        conn_dest.close()
    except Exception as e:
        abort(f"[{tabla_simple}] Error obteniendo PKs actuales en destino: {e}")
        return {"insertados": 0, "omitidos": 0}

    insertables = []
    omitidos = 0
    if pk_cols:
        for row in filas:
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
        conn_dest = pyodbc.connect(conn_str_dest, timeout=8)
        cur_dest = conn_dest.cursor()
        conn_dest.autocommit = False
        lotes = 3000  # puedes ajustarlo según tu RAM y base
        total = len(insertables)
        for i in range(0, total, lotes):
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

        cur_dest.close()
        conn_dest.close()
    except Exception as e:
        abort(f"[{tabla_simple}] Error global insertando: {e}")
        return {"insertados": 0, "omitidos": omitidos}

    log(f"[{tabla_simple}] Migración finalizada. Insertados: {total_insertados}, Omitidos por duplicado: {omitidos}")
    progress(100)
    return {"insertados": total_insertados, "omitidos": omitidos}