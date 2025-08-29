import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import pyodbc
import re
from collections import defaultdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

#styles
from styles import entrada_estandar, etiqueta_titulo, boton_accion, boton_rojo, boton_exito

CATALOGO_FILE = "catalogo_migracion.json"

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
        log(f"[{tabla}] No se pudieron desactivar índices secundarios: {e}")

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
        log(f"[{tabla}] No se pudieron reactivar índices secundarios: {e}")

def migrar_tabla_del_grupo(tabla_conf, variables, conn_str_ori, conn_str_dest, batch_size, idx_tabla, total_tablas, log, progress):
    tabla = tabla_conf.get('tabla') or tabla_conf.get('tabla llave')
    if not es_nombre_tabla_valido(tabla):
        log(f"[{tabla}] Nombre de tabla inválido/peligroso. Abortando.")
        return 0

    llave = tabla_conf.get('llave', "")
    join = tabla_conf.get('join', "")
    condicion = tabla_conf.get('condicion', "")
    where = condicion
    for var, val in variables.items():
        where = where.replace(f"${var}$", val)

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
        log(f"[{tabla}] Estructura diferente! Origen: {cols_ori} / Destino: {cols_dest}")
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
    log(f"[{tabla}] PK/índice unique detectado: {pk_cols}" if pk_cols else f"[{tabla}] ¡ATENCIÓN! No se detectó PK/índice unique. Puede haber duplicados.")

    # 3. Desactiva índices secundarios (en destino) antes de insertar
    desactivar_indices_secundarios(conn_str_dest, tabla, log)

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
            cur_ori.execute(sql)
            colnames = [d[0] for d in cur_ori.description]
            cur_dest = conn_dest.cursor()

            total_filas = 0
            lote_num = 0
            while True:
                filas = cur_ori.fetchmany(BATCH_SIZE_EXTRACCION)
                if not filas:
                    break
                total_filas += len(filas)
                lote_num += 1
                # PK indispensables
                if pk_cols:
                    # Preparar los PKs de este batch para verificar duplicados en destino
                    pk_vals_a_insertar = set(tuple(getattr(row, col) for col in pk_cols) for row in filas)
                    if pk_vals_a_insertar:
                        # Para evitar queries megagrandes, buscamos solo los PKs de este batch
                        filtros = []
                        params = []
                        for pk in pk_vals_a_insertar:
                            filtro = " AND ".join([f"{col} = ?" for col in pk_cols])
                            filtros.append(f"({filtro})")
                            params.extend(pk)
                        filtros_sql = " OR ".join(filtros)
                        query = f"SELECT {','.join(pk_cols)} FROM {tabla} WHERE {filtros_sql}" if filtros_sql else f"SELECT {','.join(pk_cols)} FROM {tabla} WHERE 1=0"
                        cur_dest.execute(query, params)
                        pks_dest = set(tuple(row) for row in cur_dest.fetchall())
                    else:
                        pks_dest = set()
                    # Prepara los insertables filtrando por PK (evitando duplicados)
                    insertables = []
                    for row in filas:
                        key = tuple(getattr(row, col) for col in pk_cols)
                        if key not in pks_dest:
                            insertables.append([getattr(row, col) for col in colnames])
                        else:
                            omitidos += 1
                else:
                    insertables = [[getattr(row, col) for col in colnames] for row in filas]

                if insertables:
                    sql_insert = f"INSERT INTO {tabla} ({','.join(colnames)}) VALUES ({','.join(['?' for _ in colnames])})"
                    try:
                        cur_dest.executemany(sql_insert, insertables)
                        migrados += len(insertables)
                        conn_dest.commit()
                        log(f"[{tabla}] Batch {lote_num} migrado: {len(insertables)} registros insertados.")
                    except Exception as e:
                        log(f"[{tabla}] Error insertando batch {lote_num}: {e}")
                        conn_dest.rollback()
                progress(
                    int(100 * (idx_tabla + min(total_filas, migrados) / max(1, total_filas)) / total_tablas)
                )
    except Exception as e:
        log(f"[{tabla}] Error global durante migración: {e}")
        reactivar_indices_secundarios(conn_str_dest, tabla, log)
        return migrados

    # 9. Reactiva índices secundarios tras el insert
    reactivar_indices_secundarios(conn_str_dest, tabla, log)
    progress(int(100 * (idx_tabla+1) / total_tablas))
    log(f"[{tabla}] FIN migración de tabla. Registros migrados: {migrados} / Omitidos (duplicados): {omitidos} / Progreso global: {idx_tabla+1}/{total_tablas}")

    return migrados

def migrar_grupo(grupo_conf, variables, amb_origen, amb_destino, log_func, progress_func, abort_func):
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
    batch_size = 5000  # Puede ajustar el tamaño del batch
    total_tablas = len(tablas)

    # Ejecutar migración de tablas en paralelo (1 tabla, 1 thread, cada tabla solo una vez)
    resultados = []
    with ThreadPoolExecutor(max_workers=min(4, total_tablas)) as executor:
        futuras = []
        for idx_tabla, tabla_conf in enumerate(tablas):
            futuras.append(executor.submit(
                migrar_tabla_del_grupo,
                tabla_conf, variables, conn_str_ori, conn_str_dest, batch_size,
                idx_tabla, total_tablas, log, progress
            ))
        for future in as_completed(futuras):
            try:
                resultados.append(future.result())
            except Exception as exc:
                log(f"ERROR GLOBAL EN POOL DE MIGRACION DE TABLAS: {exc}")

    total_global = sum(resultados)
    log(f"✅ Migración de grupo finalizada. Total migrados: {total_global}")

#################################################################
# --------- CLASES DE LA ADMINISTRACION VISUAL DE GRUPOS -------
#################################################################

class MigracionGruposGUI(tk.Toplevel):
    def __init__(self, master=None, on_update_callback=None, json_path=None):
        super().__init__(master)
        self.title("Gestión de Grupos de Migración")
        self.geometry("950x500")
        self.on_update_callback = on_update_callback
        self.json_path = json_path or CATALOGO_FILE
        self.catalogo = []
        self.current_group = None
        self.campos_tabla = []
        self.create_widgets()
        self.load_catalogo()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        etiqueta_titulo(top_frame, texto="Grupo de migración:").pack(side=tk.LEFT)
        self.combo_grupos = ttk.Combobox(top_frame, state="readonly", width=40)
        self.combo_grupos.pack(side=tk.LEFT, padx=5)
        self.combo_grupos.bind("<<ComboboxSelected>>", self.on_grupo_selected)
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
        self.btn_save = boton_exito(btn_frame, texto="Guardar Cambios", comando=self.guardar_grupo)
        self.btn_save.pack(side=tk.RIGHT)

    def load_catalogo(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.catalogo = json.load(f)
        else:
            self.catalogo = []
        grupos = [g["grupo"] for g in self.catalogo]
        self.combo_grupos["values"] = grupos
        self.combo_grupos.set("")
        self.clear_tree()
        self.current_group = None

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
        if grupo_data.get("tablas"):
            campos = set()
            for tabla_dato in grupo_data.get("tablas", []):
                for k in tabla_dato.keys():
                    campos.add(k)
            preferencia = ["tabla llave", "llave", "join", "condicion", "tabla"]
            self.campos_tabla = [c for c in preferencia if c in campos] + [c for c in sorted(campos) if c not in preferencia]
            self.tree["columns"] = self.campos_tabla
            for col in self.campos_tabla:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=210)
            for tabla_dato in grupo_data.get("tablas", []):
                fila = [tabla_dato.get(campo, "") for campo in self.campos_tabla]
                self.tree.insert("", "end", values=fila)

    def clear_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def on_tree_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        col = self.tree.identify_column(event.x)
        col_idx = int(col.replace('#', '')) - 1
        old_value = self.tree.item(item)['values'][col_idx]
        new_value = simpledialog.askstring(
            "Editar valor",
            f"Nuevo valor para {self.tree['columns'][col_idx]}:",
            initialvalue=old_value,
            parent=self
        )
        if new_value is not None:
            row_values = list(self.tree.item(item)['values'])
            row_values[col_idx] = new_value
            self.tree.item(item, values=row_values)

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

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Gestión de grupos de migración")
    app = MigracionGruposGUI(root)
    app.mainloop()