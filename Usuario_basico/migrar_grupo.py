import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import pyodbc
import time

#styles
from styles import entrada_estandar, etiqueta_titulo, boton_accion, boton_rojo, boton_exito

# --- IMPORTAR FUNCIÓN DE HISTORIAL ---
from .migrar_tabla import guardar_en_historial

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

CATALOGO_FILE = os.path.join("json", "catalogo_migracion.json")

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
    # --- REINVENCIÓN TOTAL DE LA LÓGICA DE MIGRACIÓN ---
    """🚀 MIGRACIÓN DE GRUPO ULTRA-OPTIMIZADA (ESTRATEGIA PEC: Preparar-Extraer-Cargar)"""
    log = log_func or print
    progress = progress_func or (lambda x: None)

    def _build_conn_str(amb, autocommit=False):
        # Esta función de utilidad se mantiene, ya que es correcta.
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={amb['ip']},{amb['puerto']};"
            f"DATABASE={amb['base']};"
            f"UID={amb['usuario']};"
            f"PWD={amb['clave']};"
        ) if amb['driver'] != 'Sybase ASE ODBC Driver' else (
            f"DRIVER={{{amb['driver']}}};SERVER={amb['ip']};PORT={amb['puerto']};"
            f"DATABASE={amb['base']};UID={amb['usuario']};PWD={amb['clave']};"
        )

    def _convertir_fila_para_sql(fila):
        """
        Convierte una fila de datos de pyodbc a un formato seguro para la inserción.
        Maneja explícitamente fechas y valores nulos para evitar errores de conversión implícita.
        """
        import datetime
        fila_convertida = []
        for valor in fila:
            if isinstance(valor, (datetime.datetime, datetime.date)):
                fila_convertida.append(valor.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) # Formato ODBC canónico
            else:
                fila_convertida.append(valor) # Mantiene None, str, int, etc.
        return fila_convertida

    conn_str_ori = _build_conn_str(amb_origen)
    # El destino NUNCA debe usar autocommit para cargas masivas.
    conn_str_dest = _build_conn_str(amb_destino, autocommit=False)
    tablas = grupo_conf['tablas']
    total_tablas = len(tablas)

    stats = {
        'migrados': 0,
        'errores': [],
        'omitidos': 0,
    }

    t_inicio = time.time()
    log(f"\n{'='*60}")
    log(f"🚀 INICIO MIGRACIÓN GRUPO: {grupo_conf.get('grupo', 'N/A')}")
    log(f"📊 Tablas a procesar: {total_tablas}")
    log(f"🔑 Variable: {variables}")
    log(f"{'='*60}\n")

    # --- FASE 1: PREPARAR (Una sola vez) ---
    plan_ejecucion = []
    log("1. Pre-compilando plan de ejecución...")
    for tabla_conf in tablas:
        tabla = tabla_conf.get('tabla') or tabla_conf.get('tabla llave') or ''
        if not tabla:
            stats['omitidos'] += 1
            continue

        # Construir SELECT
        columnas = tabla_conf.get('columnas', ['*'])
        columnas_str = ", ".join(columnas)
        condicion = tabla_conf.get('condicion', '')
        
        # Reemplazar variables en la condición
        params = []
        if variables and condicion:
            import re
            # --- SOLUCIÓN: Regex mucho más específico y seguro ---
            # Busca exactamente "columna = '$variable$'" (con o sin comillas simples opcionales)
            # y no interfiere con otras cláusulas como IN (...).
            pattern = re.compile(r"(\b\w+\b)\s*=\s*'?(\$\w+\$)'?")
            def replacer(match):
                col, var_placeholder = match.groups()
                var_name = var_placeholder.strip('$')
                if var_name in variables:
                    params.append(str(variables[var_name]))
                    return f"{col} = ?" # Reemplazo simple y seguro
                return match.group(0)
            condicion = pattern.sub(replacer, condicion)

        sql_select = f"SELECT {columnas_str} FROM {tabla}"
        if condicion:
            sql_select += f" WHERE {condicion}"

        # Construir INSERT
        placeholders = ",".join(["?"] * len(columnas))
        sql_insert = f"INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})"

        plan_ejecucion.append({
            "tabla": tabla,
            "select": sql_select,
            "params": params,
            "insert": sql_insert,
            "columnas": columnas
        })
    log(f"Plan listo. {len(plan_ejecucion)} tablas válidas a procesar.")

    # --- FASE 2 y 3: EXTRAER, CARGAR Y FINALIZAR ---
    try:
        # Conexión única para todo el grupo
        with pyodbc.connect(conn_str_ori, timeout=30) as conn_ori, pyodbc.connect(conn_str_dest, timeout=30) as conn_dest:
            cur_ori = conn_ori.cursor()
            cur_dest = conn_dest.cursor()

            # Activar fast_executemany para SQL Server si es posible
            try:
                cur_dest.fast_executemany = True
                log("✅ 'fast_executemany' activado para rendimiento superior.")
            except AttributeError:
                log("⚠️ 'fast_executemany' no soportado. Usando 'executemany' estándar.", "warning")

            for idx, plan in enumerate(plan_ejecucion):
                if cancelar_func and cancelar_func():
                    log("❌ Migración cancelada por el usuario")
                    break

                log(f"[{idx+1}/{len(plan_ejecucion)}] Procesando: {plan['tabla']}")
                progress(int(100 * idx / total_tablas))

                try:
                    cur_ori.execute(plan["select"], plan["params"])
                    filas = cur_ori.fetchall()

                    if not filas:
                        log(f"  ⏭️ Sin datos para migrar.")
                        continue

                    log(f"  📥 Extraídos: {len(filas)} registros. Insertando en lote...")

                    # --- SOLUCIÓN: Convertir explícitamente cada fila antes de la inserción ---
                    filas_convertidas = [
                        _convertir_fila_para_sql(fila) for fila in filas
                    ]
                    cur_dest.executemany(plan["insert"], filas_convertidas)
                    stats['migrados'] += len(filas)
                    log(f"  ✅ Lote para tabla {plan['tabla']} preparado en la transacción.")

                except Exception as e_tabla:
                    log(f"  ❌ ERROR en tabla {plan['tabla']}: {str(e_tabla)[:200]}", "error")
                    stats['errores'].append((plan['tabla'], str(e_tabla)))
                    # Si una tabla falla, se rompe el bucle para hacer rollback de todo el grupo.
                    raise Exception(f"Fallo en tabla {plan['tabla']}, abortando grupo.")

            # --- FASE 3: FINALIZAR ---
            if not (cancelar_func and cancelar_func()) and not stats['errores']:
                log("\nTodas las tablas procesadas. Realizando COMMIT final...", "success")
                conn_dest.commit()
                log("✅ COMMIT exitoso. Migración de grupo completada.", "success")
            else:
                log("\nCancelación o error detectado. Realizando ROLLBACK global...", "warning")
                conn_dest.rollback()
                log("ROLLBACK completado. No se guardaron cambios.", "warning")

            progress(100)

    except Exception as e_global:
        log(f"\n❌ ERROR CRÍTICO DE MIGRACIÓN: {e_global}", "error")
        if not stats['errores']: # Si el error fue de conexión u otro no capturado
            stats['errores'].append(("Global", str(e_global)))

    # RESUMEN FINAL
    t_total_ms = int((time.time() - t_inicio) * 1000)

    log(f"\n{'='*60}")
    log(f"✅ RESUMEN DE MIGRACIÓN")
    log(f"{'='*60}")
    log(f"📊 Tablas procesadas: {total_tablas}")
    log(f"💾 Registros migrados: {stats['migrados']}")
    log(f"⏭️ Tablas omitidas (sin config): {stats['omitidos']}")
    log(f"⏱️  Duración: {t_total_ms/1000:.1f} s")

    if stats['errores']:
        log(f"\n⚠️  ERRORES ENCONTRADOS ({len(stats['errores'])}):")
        for tabla, error in stats['errores']:
            log(f"  • {tabla}: {error}")
    else:
        log(f"\n✅ Sin errores")

    log(f"{'='*60}\n")

    # Guardar en historial
    resultado = {
        'insertados': stats['migrados'],
        'omitidos': stats['omitidos'],
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
