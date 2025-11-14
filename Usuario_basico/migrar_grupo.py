import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import pyodbc
import re
from collections import defaultdict
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

#styles
from styles import entrada_estandar, etiqueta_titulo, boton_accion, boton_rojo, boton_exito

# --- NUEVO WIDGET DE AUTOCOMPLETADO PERSONALIZADO (VERSIÓN DEFINITIVA) ---
class AutocompleteEntry(tk.Frame):
    def __init__(self, parent, completion_list, **kwargs):
        super().__init__(parent)
        
        self._completion_list = sorted(completion_list, key=str.lower)
        
        self.entry = entrada_estandar(self, **kwargs)
        self.entry.pack(fill='both', expand=True)
        self.entry.bind('<KeyRelease>', self._on_keyrelease)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Down>', self._on_arrow_down)
        self.entry.bind('<Up>', self._on_arrow_up)
        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind('<Enter>', self._on_enter)
        
        # --- LÍNEA NUEVA: Añadimos el evento de clic ---
        self.entry.bind('<Button-1>', self._on_click)
        
        self._listbox = None
        self._listbox_toplevel = None

    def _create_listbox(self):
        if self._listbox:
            return
        
        # Crea una ventana flotante para la lista
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width()
        
        self._listbox_toplevel = tk.Toplevel(self)
        self._listbox_toplevel.wm_overrideredirect(True) # Sin bordes de ventana
        self._listbox_toplevel.wm_geometry(f"{width}x150+{x}+{y}")
        
        self._listbox = tk.Listbox(self._listbox_toplevel, exportselection=False, selectmode='single')
        self._listbox.pack(fill='both', expand=True)
        self._listbox.bind('<ButtonRelease-1>', self._on_listbox_select)
        # Asegurar que no hay selección automática
        self._listbox.selection_clear(0, 'end')

    def _destroy_listbox(self):
        if self._listbox_toplevel:
            self._listbox_toplevel.destroy()
            self._listbox_toplevel = None
            self._listbox = None

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return", "Enter"):
            return
            
        value = self.entry.get()
        if value:
            hits = [item for item in self._completion_list if item.lower().startswith(value.lower())]
        else:
            hits = self._completion_list
            
        self._update_listbox(hits)

    def _update_listbox(self, items):
        if not items:
            self._destroy_listbox()
            return
            
        self._create_listbox()
        self._listbox.delete(0, 'end')
        for item in items:
            self._listbox.insert('end', item)
        # No preseleccionar automáticamente para permitir selección con mouse

    def _on_focus_out(self, event):
        # Cierra la lista si se pierde el foco
        self.after(200, self._destroy_listbox)

    def _on_listbox_select(self, event):
        if self._listbox and self._listbox.curselection():
            value = self._listbox.get(self._listbox.curselection())
            self.entry.delete(0, 'end')
            self.entry.insert(0, value)
            self._destroy_listbox()
            self.entry.icursor('end')
            self.event_generate("<<ItemSelected>>")

    # --- FUNCIÓN NUEVA: Se ejecuta al hacer clic en el campo ---
    def _on_click(self, event):
        """Muestra la lista completa si el campo está vacío."""
        if not self.entry.get():
            self._update_listbox(self._completion_list)

    def _on_enter(self, event):
        if self._listbox and self._listbox.curselection():
            self._on_listbox_select(event)
        return "break"



    def _move_selection(self, direction):
        if not self._listbox:
            self._update_listbox(self._completion_list)
            return "break"
        
        current_selection = self._listbox.curselection()
        if current_selection:
            next_idx = current_selection[0] + direction
            if 0 <= next_idx < self._listbox.size():
                self._listbox.selection_clear(0, 'end')
                self._listbox.selection_set(next_idx)
                self._listbox.activate(next_idx)
                self._listbox.see(next_idx)
        return "break"

    def _on_arrow_down(self, event):
        return self._move_selection(1)

    def _on_arrow_up(self, event):
        return self._move_selection(-1)

    # --- Métodos para que se comporte como un widget normal ---
    def get(self):
        return self.entry.get()

    def set(self, text):
        self.entry.delete(0, 'end')
        self.entry.insert(0, text)
        
    def focus_set(self):
        self.entry.focus_set()
        
    def icursor(self, index):
        self.entry.icursor(index)

CATALOGO_FILE = "catalogo_migracion.json"

def _manage_trigger(cursor, tabla, action, log_func=None):
    """
    Maneja habilitación/deshabilitación de triggers de forma segura
    action: 'DISABLE' o 'ENABLE'
    """
    if not tabla or 'ca_transaccion' not in tabla.lower():
        return  # Solo aplicar a ca_transaccion
    
    try:
        trigger_name = 'tg_ca_transaccion'
        sql = f"ALTER TABLE ca_transaccion {action} TRIGGER {trigger_name}"
        cursor.execute(sql)
        if log_func:
            status = "deshabilitado" if action == "DISABLE" else "rehabilitado"
            log_func(f"[{tabla}] 🔧 Trigger {trigger_name} {status}")
    except Exception as e:
        if log_func:
            log_func(f"[{tabla}] ⚠️ Error {action.lower()} trigger: {str(e)[:50]}")

def es_nombre_tabla_valido(nombre):
    # Permite solo letras, números, guion bajo y punto, sin espacios ni caracteres especiales
    return bool(re.match(r'^[A-Za-z0-9_.]+$', nombre or ''))

def columnas_tabla(conn_str, tabla):
    if not es_nombre_tabla_valido(tabla):
        raise ValueError(f"Nombre de tabla no válido: {tabla}")
    query = f"SELECT * FROM {tabla} WHERE 1=0"
    with pyodbc.connect(conn_str, timeout=8) as conn:
        cur = conn.cursor()
        try:
            cur.execute(query)
            cols = [desc[0] for desc in cur.description]
            return cols
        except Exception as e:
            raise RuntimeError(f"Error obteniendo columnas de {tabla}: {e}")

def pk_tabla(conn_str, tabla, is_sybase):
    if not es_nombre_tabla_valido(tabla):
        raise ValueError(f"Nombre de tabla no válido: {tabla}")
    partes = tabla.split('.')
    nombre_tb_simple = partes[-1]
    pk_cols = []
    try:
        with pyodbc.connect(conn_str, timeout=8, autocommit=True) as conn:
            cur = conn.cursor()
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
    except Exception as e:
        raise RuntimeError(f"Error obteniendo PK de {tabla}: {e}")
    return pk_cols

def desactivar_indices_secundarios(conn_str, tabla, log):
    """Desactiva todos los índices que no sean PK/clustered (sólo SQL Server soportado aquí)"""
    try:
        with pyodbc.connect(conn_str, timeout=8, autocommit=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT name FROM sys.indexes 
                WHERE object_id = OBJECT_ID(?) 
                  AND is_primary_key = 0 
                  AND is_unique_constraint = 0 
                  AND type_desc <> 'HEAP'
            """, (tabla,))
            idxs = [row[0] for row in cur.fetchall()]
            for idx in idxs:
                cur.execute(f"ALTER INDEX [{idx}] ON [{tabla}] DISABLE")
            if idxs:
                log(f"[{tabla}] Se desactivaron índices secundarios: {idxs}")
    except Exception as e:
        # Mensaje más claro: esto es normal en Sybase, solo funciona en SQL Server
        log(f"[{tabla}] ℹ️ Optimización de índices no disponible (normal en Sybase): {str(e)[:100]}...")

def _get_column_types(conn_str, tabla):
    """Devuelve un diccionario de {nombre_col: tipo_pyodbc} para una tabla."""
    if not es_nombre_tabla_valido(tabla):
        return {}
    try:
        with pyodbc.connect(conn_str, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {tabla} WHERE 1=0")
            return {col[0].lower(): col[1] for col in cursor.description}
    except Exception as e:
        logging.warning(f"No se pudieron obtener los tipos de columna para '{tabla}': {e}")
        return {}

def reactivar_indices_secundarios(conn_str, tabla, log):
    try:
        with pyodbc.connect(conn_str, timeout=8, autocommit=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT name FROM sys.indexes 
                WHERE object_id = OBJECT_ID(?) 
                  AND is_primary_key = 0 
                  AND is_unique_constraint = 0 
                  AND type_desc <> 'HEAP'
            """, (tabla,))
            idxs = [row[0] for row in cur.fetchall()]
            for idx in idxs:
                cur.execute(f"ALTER INDEX [{idx}] ON [{tabla}] REBUILD")
            if idxs:
                log(f"[{tabla}] Se reactivaron índices secundarios: {idxs}")
    except Exception as e:
        log(f"[{tabla}] ℹ️ Optimización de índices no disponible (normal en Sybase): {str(e)[:100]}...")

def migrar_tabla_del_grupo(
        tabla_conf,
        variables,
        conn_str_ori,
        conn_str_dest,
        batch_size,
        idx_tabla,
        total_tablas,
        log, progress,
        cancelar_func=None,
        contadores=None):

    def _sanitizar_valor(valor, tipo_columna):
        """Limpia un valor para que sea compatible con el tipo de columna de destino."""
        if isinstance(valor, str):
            # Para tipos monetarios, eliminar '$' y ','
            if tipo_columna in (pyodbc.SQL_DECIMAL, pyodbc.SQL_NUMERIC, pyodbc.SQL_REAL, pyodbc.SQL_FLOAT, pyodbc.SQL_DOUBLE):
                return valor.replace('$', '').replace(',', '').strip()
        return valor
    
    tabla = tabla_conf.get('tabla') or tabla_conf.get('tabla llave')
    if not es_nombre_tabla_valido(tabla):
        log(f"[{tabla}] Nombre de tabla inválido/peligroso. Abortando.")
        return 0

    llave = tabla_conf.get('llave', "")
    join = tabla_conf.get('join', "")
    condicion = tabla_conf.get('condicion', "")
    
    # --- CORRECCIÓN: Usar consultas parametrizadas y corregir literales ---
    params = []
    where = condicion

    # 1. Sustituir variables por '?' para parametrización
    if variables:
        # Usar regex para encontrar todas las variables como $var$
        for var_match in re.finditer(r'\$(\w+)\$', where):
            var_name = var_match.group(1)
            if var_name in variables:
                # Reemplazar la variable por '?' y añadir el valor a la lista de parámetros
                where = where.replace(var_match.group(0), '?', 1)
                # --- SOLUCIÓN DEFINITIVA: Enviar siempre como string ---
                # Se deja que el driver ODBC maneje la conversión al tipo de dato correcto de la columna.
                params.append(variables[var_name])

    # 2. Si no se usaron parámetros, intentar corregir literales de string sin comillas
    if not params and where:
        col_types = _get_column_types(conn_str_ori, tabla)
        if col_types:
            string_types = (
                pyodbc.SQL_CHAR, pyodbc.SQL_VARCHAR, pyodbc.SQL_LONGVARCHAR,
                pyodbc.SQL_WCHAR, pyodbc.SQL_WVARCHAR, pyodbc.SQL_WLONGVARCHAR,
                pyodbc.SQL_TYPE_DATE, pyodbc.SQL_TYPE_TIME, pyodbc.SQL_TYPE_TIMESTAMP
            )
            
            # Regex para encontrar `columna = valor` (o similar) donde valor es un literal sin comillas.
            pattern = re.compile(r"([a-zA-Z0-9_]+)\s*(=|!=|<>|LIKE)\s*([a-zA-Z0-9_]+)")

            def quote_replacer(match):
                col, op, val = match.groups()
                
                # Heurística: si el nombre de la columna existe y el valor no es un nombre de columna,
                # y el tipo de la columna es string, entonces añadir comillas.
                if col.lower() in col_types and val.lower() not in col_types:
                    col_type = col_types.get(col.lower())
                    if col_type in string_types:
                        return f"{col} {op} '{val}'" # Añadir comillas
                
                return match.group(0) # Devolver sin cambios si no cumple las condiciones

            where = pattern.sub(quote_replacer, where)

    log(f"[{tabla}] INICIO migración de tabla ({idx_tabla+1}/{total_tablas})")
    progress(int(100 * (idx_tabla) / total_tablas))

    # 1. Validar estructura
    try:
        cols_ori = columnas_tabla(conn_str_ori, tabla)
        cols_dest = columnas_tabla(conn_str_dest, tabla)
    except Exception as e:
        log(f"[{tabla}] Error consultando columnas: {e}")
        return 0
    if cols_ori != cols_dest:
        log(f"[{tabla}] ⚠️ Estructura diferente! Origen: {cols_ori} / Destino: {cols_dest}")
        if contadores:
            contadores['estructura_diferente'] += 1
            contadores['tablas_estructura_diferente'].append(tabla)
        return 0
    else:
        log(f"[{tabla}] ✅ Estructura igual en origen y destino.")

    # 2. Detectar PK o índice unique
    pk_cols = []
    try:
        pk_cols = pk_tabla(conn_str_ori, tabla, True)
    except Exception as e:
        log(f"[{tabla}] Advertencia: Error detectando PK: {e}")
        pk_cols = []
    if pk_cols:
        log(f"[{tabla}] PK/índice unique detectado: {pk_cols}")
    else:
        log(f"[{tabla}] ⚠️ Sin PK/índice unique detectado. Posibles duplicados.")
        if contadores:
            contadores['sin_pk'] += 1
            contadores['tablas_sin_pk'].append(tabla)

    # 3. Desactiva índices secundarios (en destino) antes de insertar
    desactivar_indices_secundarios(conn_str_dest, tabla, log)

    tipos_col_dest = _get_column_types(conn_str_dest, tabla)


    # 4. Armar SQL extracción
    sql = ""
    if llave and join:
        tablas_llave = [t.strip() for t in llave.split(",")]
        if len(tablas_llave) == 1:
            sql = f"SELECT tbl.* FROM {tabla} tbl JOIN {tablas_llave[0]} ON {join}"
            if where:
                sql += f" WHERE {where}"
        else:
            sql = f"SELECT tbl.* FROM {tabla} tbl"
            for t in tablas_llave:
                sql += f", {t}"
            condiciones = []
            if join:
                condiciones.append(join)
            if where:
                condiciones.append(where)
            if condiciones:
                sql += " WHERE " + " AND ".join(condiciones)
    else:
        sql = f"SELECT * FROM {tabla}"
        if where:
            sql += f" WHERE {where}"

    log(f"[{tabla}] SQL de extracción: {sql}")

    # 5. Proceso por lotes para optimización de performance
    migrados = 0
    omitidos = 0
    BATCH_SIZE_EXTRACCION = 1000
    try:
        with pyodbc.connect(conn_str_ori, timeout=60) as conn_ori, \
             pyodbc.connect(conn_str_dest, timeout=60, autocommit=False) as conn_dest:

            cur_ori = conn_ori.cursor()
            cur_ori.execute(sql, params)
            colnames = [d[0] for d in cur_ori.description]
            cur_dest = conn_dest.cursor()

            total_filas = 0
            lote_num = 0
            while True:
                filas = cur_ori.fetchmany(BATCH_SIZE_EXTRACCION)
                if not filas:
                    break
                if cancelar_func and cancelar_func():
                    log(f"[{tabla}] Migracion  de grupo cancelada por el usuario. rollback de cambios si es necesario.")
                    
                    # REHABILITAR TRIGGER AL CANCELAR
                    _manage_trigger(cur_dest, tabla, "ENABLE", log)
                    
                    try:
                        conn_dest.rollback()
                    except Exception:
                        pass
                    return migrados
                
                total_filas += len(filas)
                lote_num += 1
                
                # --- LÓGICA DE VERIFICACIÓN DE DUPLICADOS REFACTORIZADA ---
                if pk_cols:
                    pks_dest = set()
                    pk_types = {col: tipos_col_dest.get(col.lower()) for col in pk_cols}
                    
                    # Usar tabla temporal para una verificación de duplicados más robusta
                    temp_table_name = f"##pks_check_{os.getpid()}_{threading.get_ident()}"
                    try:
                        # 1. Crear tabla temporal
                        col_defs = []
                        for col in pk_cols:
                            # Mapeo simple de tipos de Python a SQL
                            sql_type = "VARCHAR(255)" # Default
                            py_type = pk_types.get(col)
                            if py_type in (pyodbc.SQL_INTEGER, pyodbc.SQL_BIGINT): sql_type = "INT"
                            elif py_type in (pyodbc.SQL_DECIMAL, pyodbc.SQL_NUMERIC): sql_type = "DECIMAL(18,2)"
                            elif py_type == pyodbc.SQL_CHAR: sql_type = "CHAR(10)"
                            col_defs.append(f"{col} {sql_type}")
                        
                        cur_dest.execute(f"CREATE TABLE {temp_table_name} ({', '.join(col_defs)})")

                        # 2. Insertar PKs del lote en la tabla temporal
                        pks_del_lote = [tuple(getattr(row, col) for col in pk_cols) for row in filas]
                        if pks_del_lote:
                            cur_dest.executemany(f"INSERT INTO {temp_table_name} VALUES ({','.join(['?']*len(pk_cols))})", pks_del_lote)

                            # 3. Hacer JOIN para encontrar duplicados
                            join_cond = " AND ".join([f"t1.{col} = t2.{col}" for col in pk_cols])
                            select_dups_sql = f"SELECT t1.* FROM {temp_table_name} t1 JOIN {tabla} t2 ON {join_cond}"
                            pks_dest = set(tuple(row) for row in cur_dest.execute(select_dups_sql).fetchall())
                    finally:
                        # 4. Asegurarse de eliminar la tabla temporal
                        cur_dest.execute(f"DROP TABLE {temp_table_name}")

                    # Prepara los insertables filtrando por PK (evitando duplicados)
                    insertables = []
                    for row in filas:
                        # --- MEJORA: Verificar cancelación en cada registro para una respuesta más rápida ---
                        if cancelar_func and cancelar_func():
                            break # Salir del bucle de filas

                        key = tuple(getattr(row, col) for col in pk_cols)
                        if key not in pks_dest:
                            # --- MEJORA: Sanitizar cada valor antes de añadirlo a la lista de inserción ---
                            fila_sanitizada = []
                            for col in colnames:
                                fila_sanitizada.append(_sanitizar_valor(getattr(row, col), tipos_col_dest.get(col.lower())))
                            insertables.append(fila_sanitizada)
                        else:
                            omitidos += 1
                else:
                    insertables = [[getattr(row, col) for col in colnames] for row in filas]

                if insertables:
                    # DESHABILITAR TRIGGER ANTES DE INSERTAR
                    _manage_trigger(cur_dest, tabla, "DISABLE", log)
                    
                    sql_insert = f"INSERT INTO {tabla} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})"
                    try:
                        cur_dest.executemany(sql_insert, insertables)
                        migrados += len(insertables)
                        conn_dest.commit()
                        log(f"[{tabla}] Batch {lote_num} migrado: {len(insertables)} registros insertados.")
                        
                        # REHABILITAR TRIGGER TRAS INSERCIÓN EXITOSA
                        _manage_trigger(cur_dest, tabla, "ENABLE", log)
                        
                    except Exception as e:
                        # REHABILITAR TRIGGER EN CASO DE ERROR
                        _manage_trigger(cur_dest, tabla, "ENABLE", log)
                        
                        log(f"[{tabla}] Error insertando batch {lote_num}: {e}")
                        conn_dest.rollback()
                progress(
                    int(100 * (idx_tabla + min(total_filas, migrados) / max(1, total_filas)) / total_tablas)
                )
    except Exception as e:
        log(f"[{tabla}] Error global durante migración: {e}")
        
        # ASEGURAR QUE EL TRIGGER ESTÉ HABILITADO EN CASO DE ERROR GLOBAL
        try:
            with pyodbc.connect(conn_str_dest, timeout=8) as conn_dest_cleanup:
                cur_dest_cleanup = conn_dest_cleanup.cursor()
                _manage_trigger(cur_dest_cleanup, tabla, "ENABLE", log)
        except Exception:
            pass
        
        reactivar_indices_secundarios(conn_str_dest, tabla, log)
        return migrados

    # 9. Asegurar que el trigger esté habilitado al finalizar
    try:
        with pyodbc.connect(conn_str_dest, timeout=8) as conn_dest_final:
            cur_dest_final = conn_dest_final.cursor()
            _manage_trigger(cur_dest_final, tabla, "ENABLE", log)
    except Exception:
        pass
    
    # 10. Reactiva índices secundarios tras el insert
    reactivar_indices_secundarios(conn_str_dest, tabla, log)
    progress(int(100 * (idx_tabla+1) / total_tablas))
    log(f"[{tabla}] FIN migración de tabla. Registros migrados: {migrados} / Omitidos (duplicados): {omitidos} / Progreso global: {idx_tabla+1}/{total_tablas}")

    return migrados

def migrar_grupo(
        grupo_conf,
        variables,
        amb_origen,
        amb_destino,
        log_func,
        progress_func,
        abort_func,
        cancelar_func=None
    ):
    log = log_func if log_func else print
    progress = progress_func if progress_func else lambda x: None
    abort = abort_func if abort_func else lambda msg: print(f"ABORT: {msg}")
    
    # Contadores para el resumen final
    contadores = {
        'estructura_diferente': 0,
        'sin_pk': 0,
        'total_tablas': 0,
        'tablas_estructura_diferente': [],
        'tablas_sin_pk': []
    }

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
    batch_size = 5000  # Puede ajustar el tamaño del batch
    total_tablas = len(tablas)
    contadores['total_tablas'] = total_tablas

    # Ejecutar migración de tablas en paralelo (1 tabla, 1 thread, cada tabla solo una vez)
    resultados = []
    with ThreadPoolExecutor(max_workers=min(4, total_tablas)) as executor:
        futuras = []
        for idx_tabla, tabla_conf in enumerate(tablas):
            futuras.append(executor.submit(
                migrar_tabla_del_grupo,
                tabla_conf, variables, conn_str_ori, conn_str_dest, batch_size,
                idx_tabla, total_tablas, log, progress, cancelar_func, contadores
            ))
        for future in as_completed(futuras):
            try:
                resultados.append(future.result())
            except Exception as exc:
                log(f"ERROR GLOBAL EN POOL DE MIGRACION DE TABLAS: {exc}")

    total_global = sum(resultados)
    
    # Resumen final detallado
    log("\n" + "="*60)
    log(f"✅ RESUMEN DE MIGRACIÓN DE GRUPO '{grupo_conf.get('grupo', 'N/A')}'")
    log("="*60)
    log(f"📊 Total de tablas procesadas: {contadores['total_tablas']}")
    log(f"💾 Total de registros migrados: {total_global}")
    
    if contadores['estructura_diferente'] > 0:
        log(f"⚠️  Tablas con estructura diferente: {contadores['estructura_diferente']}")
        for tabla in contadores['tablas_estructura_diferente']:
            log(f"    • {tabla}")
    else:
        log(f"✅ Todas las tablas tienen estructura compatible")
    
    if contadores['sin_pk'] > 0:
        log(f"⚠️  Tablas sin PK/índice unique: {contadores['sin_pk']} (riesgo de duplicados)")
    else:
        log(f"✅ Todas las tablas tienen PK/índice unique")
    
    log(f"ℹ️  Nota: Los errores de optimización de índices son normales en Sybase")
    log("="*60)

    return {'insertados': total_global, 'omitidos': 0, 'errores': contadores['estructura_diferente']}

#################################################################
# -------- CLASES DE LA ADMINISTRACION VISUAL DE GRUPOS ------- #
#################################################################

class MigracionGruposGUI(tk.Toplevel):
    
    def __init__(self, master=None, on_update_callback=None, json_path=None, grupo_inicial=None):
        super().__init__(master)
        self.title("Gestión de Grupos de Migración")
        self.geometry("950x500")
        self.on_update_callback = on_update_callback
        self.json_path = json_path or CATALOGO_FILE
        self.grupo_inicial = grupo_inicial  # <-- Línea nueva
        self.catalogo = []
        self.current_group = None
        self.campos_tabla = []
        self.create_widgets()
        self.load_catalogo()
         # --- FOCO INICIAL Y POSICIÓN DEL CURSOR ---
        self.after(100, self.establecer_foco_inicial)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def establecer_foco_inicial(self):
        """Pone el foco en el entry y el cursor al inicio."""
        self.combo_grupos.focus_set()
        self.combo_grupos.icursor(0)

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        etiqueta_titulo(top_frame, texto="Grupo de migración:").pack(side=tk.LEFT)
        # Usamos nuestro nuevo widget
        self.combo_grupos = AutocompleteEntry(top_frame, completion_list=[], width=25)
        self.combo_grupos.pack(side=tk.LEFT, padx=5)
        # --- CORRECCIÓN 1: Escuchar el nuevo evento <<ItemSelected>> ---
        self.combo_grupos.bind("<<ItemSelected>>", self.on_grupo_selected)
        btn_add = boton_accion(top_frame, texto="Agregar nuevo grupo", comando=self.nuevo_grupo)
        btn_add.pack(side=tk.RIGHT)
        detalles_frame = tk.LabelFrame(self, text="Tablas del grupo (doble clic para editar/añadir/eliminar):")
        detalles_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree = ttk.Treeview(detalles_frame, columns=(), show="headings", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        scrollbar = tk.Scrollbar(detalles_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        self.btn_add_tabla = boton_accion(btn_frame, texto="Añadir tabla a grupo", comando=self.nueva_tabla)
        self.btn_add_tabla.pack(side=tk.LEFT)
        self.btn_delete_tabla = boton_rojo(btn_frame, texto="Eliminar tabla seleccionada", comando=self.eliminar_tabla)
        self.btn_delete_tabla.pack(side=tk.LEFT, padx=20)

        # --- BOTONES DE LA DERECHA ---
        self.btn_save = boton_exito(btn_frame, texto="Guardar Cambios", comando=self.guardar_grupo)
        self.btn_save.pack(side=tk.RIGHT)
        
        # --- NUEVO BOTÓN SALIR ---
        self.btn_salir = boton_accion(btn_frame, texto="Salir", comando=self.on_close)
        self.btn_salir.pack(side=tk.RIGHT, padx=5)

    def load_catalogo(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.catalogo = json.load(f)
        else:
            self.catalogo = []
        grupos = [g["grupo"] for g in self.catalogo]
        self.combo_grupos._completion_list = sorted(grupos, key=str.lower)
        
        # 1. Limpiamos la vista primero
        self.clear_tree()
        self.current_group = None
        
        # 2. Ahora, si hay un grupo inicial, lo seleccionamos
        if self.grupo_inicial and self.grupo_inicial in grupos:
            self.combo_grupos.set(self.grupo_inicial)
            self.on_grupo_selected() # Esto cargará la grilla
        else:
            self.combo_grupos.set("")

    def on_grupo_selected(self, event=None):
        grupo_seleccionado = self.combo_grupos.get()
        grupo_data = next((g for g in self.catalogo if g["grupo"] == grupo_seleccionado), None)
        if grupo_data:
            self.current_group = grupo_data
            self.populate_group_details(grupo_data)
        else:
            self.current_group = None
            self.clear_tree()

    def populate_group_details(self, grupo_data):
        self.clear_tree()
        self.campos_tabla = []
        tablas_del_grupo = grupo_data.get("tablas", [])
        if tablas_del_grupo:
            # --- CORRECCIÓN: Ordenar los datos antes de mostrarlos ---
            # 1er criterio: 'tabla' o 'tabla llave', 2do criterio: 'llave'
            tablas_ordenadas = sorted(
                tablas_del_grupo,
                key=lambda item: (str(item.get('tabla', item.get('tabla llave', ''))).lower(), str(item.get('llave', '')).lower())
            )

            campos = set()
            for tabla_dato in tablas_ordenadas:
                for k in tabla_dato.keys():
                    campos.add(k)
            # --- CORRECCIÓN: Establecer el orden de columnas solicitado ---
            preferencia = ["tabla", "llave", "join", "condicion"]
            self.campos_tabla = [c for c in preferencia if c in campos] + [c for c in sorted(campos) if c not in preferencia]
            self.tree["columns"] = self.campos_tabla
            for col in self.campos_tabla:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=210)
            for tabla_dato in tablas_ordenadas:
                fila = [tabla_dato.get(campo, "") for campo in self.campos_tabla]
                self.tree.insert("", "end", values=fila)

    def clear_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    # --- CORRECCIÓN 2: Diálogo de edición mejorado ---
    def on_tree_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        col = self.tree.identify_column(event.x)
        col_idx = int(col.replace('#', '')) - 1
        
        # Crear un Toplevel personalizado para la edición
        dlg = tk.Toplevel(self)
        dlg.title(f"Editar '{self.tree['columns'][col_idx]}'")
        dlg.transient(self)
        dlg.grab_set()
        
        # --- CORRECCIÓN: Combinar tamaño y posición en una sola llamada a geometry() ---
        ancho_dlg = 450
        alto_dlg = 160
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (ancho_dlg // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (alto_dlg // 2)
        dlg.geometry(f"{ancho_dlg}x{alto_dlg}+{x}+{y}")
        
        etiqueta_titulo(dlg, texto=f"Nuevo valor para '{self.tree['columns'][col_idx]}':").pack(pady=5)
        
        # Usar un Text widget para contenido largo
        text_widget = tk.Text(dlg, wrap="word", height=4, width=60)
        text_widget.pack(pady=5, padx=10, fill="both", expand=True)
        old_value = self.tree.item(item)['values'][col_idx]
        text_widget.insert("1.0", old_value)
        
        new_value = None
        def on_ok():
            nonlocal new_value
            new_value = text_widget.get("1.0", "end-1c").strip()
            dlg.destroy()

        # --- CORRECCIÓN 2: Añadir botones de Aceptar y Cancelar ---
        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=10)
        boton_exito(btn_frame, texto="Aceptar", comando=on_ok).pack(side=tk.LEFT, padx=10)
        boton_rojo(btn_frame, texto="Cancelar", comando=dlg.destroy).pack(side=tk.LEFT, padx=10)

        self.wait_window(dlg)

        # --- Lógica de guardado (ya estaba correcta) ---
        # --- LÓGICA DE GUARDADO CORREGIDA ---
        if new_value is not None:
            # 1. Actualiza la vista en la grilla (Treeview)
            row_values = list(self.tree.item(item)['values'])
            row_values[col_idx] = new_value
            self.tree.item(item, values=row_values)

            # 2. Actualiza los datos en memoria para que se guarden en el JSON
            if self.current_group and 'tablas' in self.current_group:
                # Encuentra el índice de la fila en la grilla
                row_index = self.tree.index(item)
                # Asegúrate de que el índice sea válido para la lista de tablas
                if 0 <= row_index < len(self.current_group['tablas']):
                    col_name = self.campos_tabla[col_idx]
                    self.current_group['tablas'][row_index][col_name] = new_value

    def nueva_tabla(self):
        campos = self.campos_tabla if self.campos_tabla else ["tabla llave", "llave", "join", "condicion"]
        dlg = TablaDialog(self, campos=campos)
        self.wait_window(dlg)
        if dlg.result:
            self.tree.insert("", "end", values=dlg.result)

    def eliminar_tabla(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una tabla para eliminar.")
            return
        self.tree.delete(sel[0])

    def guardar_grupo(self):
        if not self.current_group:
            messagebox.showerror("Error", "Selecciona un grupo para editar/guardar.")
            return
        nuevas_tablas = []
        for row in self.tree.get_children():
            valores = self.tree.item(row)['values']
            tabla_dicc = {campo: valor for campo, valor in zip(self.campos_tabla, valores)}
            nuevas_tablas.append(tabla_dicc)
        self.current_group["tablas"] = nuevas_tablas
        self.save_catalogo()
        messagebox.showinfo("Éxito", "El grupo ha sido actualizado en el catálogo.")

    def save_catalogo(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.catalogo, f, indent=2, ensure_ascii=False)
        self.load_catalogo()

    def nuevo_grupo(self):
        nombre = simpledialog.askstring("Nuevo Grupo", "Nombre del nuevo grupo:", parent=self)
        if not nombre:
            return
        if any(g['grupo'].lower() == nombre.lower() for g in self.catalogo):
            messagebox.showerror("Error", f"Ya existe un grupo con ese nombre: {nombre}") 
            return
        campos = ["tabla llave", "llave", "join", "condicion"]
        tablas = []
        while True:
            dlg = TablaDialog(self, campos=campos)
            self.wait_window(dlg)
            if dlg.result:
                tablas.append({k: v for k, v in zip(campos, dlg.result)})
            else:
                break
            agregar_otra = messagebox.askyesno("Añadir tabla", "¿Desea agregar otra tabla a este grupo?", parent=self)
            if not agregar_otra:
                break
        if not tablas:
            messagebox.showwarning("Aviso", "No se añadió ninguna tabla. El grupo no será creado.")
            return
        nuevo = {"grupo": nombre, "tablas": tablas}
        self.catalogo.append(nuevo)
        self.save_catalogo()
        self.combo_grupos.set(nombre)
        self.on_grupo_selected()

    def on_close(self):
        if self.on_update_callback:
            self.on_update_callback()
        
        self.master.grab_set()
        self.destroy()

class TablaDialog(tk.Toplevel):
    def __init__(self, parent, campos=None):
        super().__init__(parent)
        self.result = None
        self.title("Agregar/Editar tabla de grupo")
        self.campos = campos or ["tabla llave", "llave", "join", "condicion"]
        self.entries = []
        anchura = 400 + (len(self.campos) - 4) * 90
        altura = 110 + len(self.campos) * 32
        self.geometry(f"{anchura}x{altura}")
        self.resizable(0, 0)
        self.init_widgets()
        self.grab_set()
        self.focus_force()
        self.transient(parent)

    def init_widgets(self):
        for idx, campo in enumerate(self.campos):
            etiqueta_titulo(self, texto=f"{campo}:").grid(row=idx, column=0, sticky=tk.W, padx=5, pady=6)
            entry = tk.Entry(self, width=52)
            entry.grid(row=idx, column=1, padx=5, pady=6)
            self.entries.append(entry)
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=len(self.campos), column=0, columnspan=2, pady=8)
        btn_ok = boton_accion(btn_frame, texto="OK", width=10, comando=self.accept)
        btn_ok.pack(side=tk.LEFT, padx=5)
        btn_cancel = boton_accion(btn_frame, texto="Cancelar", width=10, comando=self.cancel)
        btn_cancel.pack(side=tk.LEFT, padx=5)

    def accept(self):
        vals = [e.get().strip() for e in self.entries]
        if not vals[0]:
            messagebox.showerror("Error", f"Debe ingresar {self.campos[0]}.")
            return
        self.result = vals
        self.destroy()

    def cancel(self):
        self.destroy()
