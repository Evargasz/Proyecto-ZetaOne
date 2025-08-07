from tkinter import Toplevel, ttk, messagebox
import tkinter as tk
import datetime
from Usuario_administrador.handlers.validacion import validar_archivos_multiambiente
from Usuario_administrador.handlers.catalogacion import catalogar_archivos_multiambiente, mostrar_resultado_catalogacion
from Usuario_administrador.styles import FUENTE_GENERAL, FUENTE_BOTON

def centrar_ventana(win, width, height, parent=None):
    win.update_idletasks()
    if parent is not None:
        root_parent = parent.winfo_toplevel()
        root_parent.update_idletasks()
        x0 = root_parent.winfo_rootx()
        y0 = root_parent.winfo_rooty()
        pw = root_parent.winfo_width()
        ph = root_parent.winfo_height()
        x = x0 + (pw // 2) - (width // 2)
        y = y0 + (ph // 2) - (height // 2) - 20
    else:
        pantalla_ancho = win.winfo_screenwidth()
        pantalla_alto = win.winfo_screenheight()
        x = (pantalla_ancho // 2) - (width // 2)
        y = (pantalla_alto // 2) - (height // 2) - 20
    win.geometry(f"{width}x{height}+{x}+{y}")

def logear(parent, msg):
    try:
        if hasattr(parent, 'master') and hasattr(parent.master, 'arch_panel'):
            arch_panel = parent.master.arch_panel
            if hasattr(arch_panel, "logtxt"):
                arch_panel.logtxt.insert(tk.END, msg + "\n")
                arch_panel.logtxt.see(tk.END)
        elif hasattr(parent, "logtxt"):
            parent.logtxt.insert(tk.END, msg + "\n")
            parent.logtxt.see(tk.END)
        else:
            print(msg)
    except Exception as e:
        print(f"(No se pudo loguear en widget) {msg}")

def lanzar_validacion(parent, archivos_unicos, seleccionados_idx, ambientes_panel):
    try:
        ambientes = ambientes_panel.get_seleccionados() if hasattr(ambientes_panel, 'get_seleccionados') else [ambientes_panel.ambientes[i] for i in ambientes_panel.lbamb.curselection()]
        if not ambientes:
            messagebox.showwarning("Ambiente", "Seleccione al menos un ambiente con conexión OK.", parent=parent)
            logear(parent, "[VALIDACIÓN] Selección de ambientes vacía o inválida.")
            return

        if not seleccionados_idx:
            messagebox.showwarning("Validación", "Seleccione al menos un archivo para validar.", parent=parent)
            logear(parent, "[VALIDACIÓN] Selección de archivos vacía.")
            return

        progreso_win = tk.Toplevel(parent)
        progreso_win.withdraw()  # Oculta la ventana al inicio
        progreso_win.title("Validando archivos contra Sybase...")
        progreso_win.resizable(False, False)
        progreso_win.transient(parent)
        progreso_win.grab_set()
        progreso_win.configure(bg="#fffef4")

        tk.Label(
            progreso_win, 
            text="Validando archivos contra Sybase...", 
            font=FUENTE_BOTON, 
            pady=15, 
            bg="#fffef4"
        ).pack()

        total_tareas = len(seleccionados_idx) * len(ambientes)
        progress = ttk.Progressbar(
            progreso_win, 
            orient="horizontal", 
            length=350, 
            mode="determinate", 
            maximum=max(total_tareas, 1), 
            style="ProgressYellow.Horizontal.TProgressbar"
        )
        progress.pack(pady=(8, 2))

        label_porc = tk.Label(
            progreso_win, 
            text="0 %", 
            font=("Segoe UI", 11), 
            bg="#fffef4", 
            fg="#efad00"
        )
        label_porc.pack()

        progreso_win.update_idletasks()

        # CENTRAR la ventana y mostrarla ya completamente formada
        ancho = progreso_win.winfo_width()
        alto = progreso_win.winfo_height()
        pantalla_ancho = progreso_win.winfo_screenwidth()
        pantalla_alto = progreso_win.winfo_screenheight()
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        progreso_win.geometry(f"+{x}+{y}")
        progreso_win.deiconify()
        progreso_win.lift()

        logear(parent, f"[VALIDACIÓN] Iniciando validación: Archivos seleccionados={len(seleccionados_idx)}, Ambientes={', '.join(a['nombre'] for a in ambientes)}")

        resultados = validar_archivos_multiambiente_feedback(
            archivos_unicos, seleccionados_idx, ambientes, progress, label_porc, progreso_win, parent
        )
        progreso_win.destroy()
        logear(parent, f"[VALIDACIÓN] Validación finalizada. Total resultados: {len(resultados)}")
        mostrar_resultado(parent, resultados, archivos_unicos, ambientes_panel)
    except Exception as e:
        import traceback
        messagebox.showerror("Error crítico", f"Ocurrió un error en el proceso de validación:\n{e}")
        logear(parent, "[VALIDACIÓN] ERROR crítico:\n" + traceback.format_exc())

def validar_archivos_multiambiente_feedback(archivos_unicos, seleccionados_idx, ambientes, progress, label_porc, progreso_win, parent):
    from Usuario_administrador.extra_sp_utils import ultra_extraer_sp_bd, limpiar_identificador
    from Usuario_administrador.handlers.catalogacion import validar_archivo_sp_local_vs_sybase
    resultados_fila = []
    contador = 0
    total_tareas = max(len(seleccionados_idx) * len(ambientes), 1)
    for idx in seleccionados_idx:
        arch = archivos_unicos[idx]
        fecha_local = datetime.datetime.fromtimestamp(arch['fecha_mod'])
        if arch['tipo'] == 'sp':
            stored_proc, base_datos = ultra_extraer_sp_bd(arch['path'])
            if isinstance(stored_proc, str):
                stored_proc = limpiar_identificador(stored_proc)
            if isinstance(base_datos, str):
                base_datos = limpiar_identificador(base_datos)
        else:
            stored_proc, base_datos = ("-", "-")
        for amb in ambientes:
            try:
                if arch['tipo'] == 'sp' and stored_proc != "No encontrado" and base_datos != "No encontrado":
                    fecha_sybase_str, fecha_sybase = validar_archivo_sp_local_vs_sybase(arch, amb, stored_proc, base_datos)
                else:
                    fecha_sybase_str = "No existe"
            except Exception as ex:
                fecha_sybase_str = "Error"
                logear(parent, f"[VALIDACIÓN][ERROR] {arch['nombre_archivo']} ({amb['nombre']}): {ex}")
            row = (
                str(contador+1),
                amb['nombre'],
                arch['rel_path'],
                fecha_local.strftime('%Y-%m-%d %H:%M'),
                base_datos if base_datos else "-",
                stored_proc if stored_proc else "-",
                fecha_sybase_str
            )
            resultados_fila.append(row)
            contador += 1
            porc = int((contador / total_tareas) * 100)
            progress['value'] = contador
            label_porc.config(text=f"{porc} %")
            progreso_win.update_idletasks()
    return resultados_fila

def mostrar_resultado(parent, resultados, archivos_unicos, ambientes_panel):
    win = Toplevel(parent)
    win.title("Resultado validación multiambiente")
    ancho, alto = 1200, 670
    win.update_idletasks()
    centrar_ventana(win, ancho, alto, parent=None)

    columns = ("No.", "Ambiente", "Archivo", "F. Local", "BD", "SP", "F. Sybase")
    ancho_columnas = [45, 130, 360, 120, 100, 190, 200]
    tree = ttk.Treeview(win, columns=columns, show="headings", height=18, selectmode="extended")
    for col, ancho_ in zip(columns, ancho_columnas):
        tree.heading(col, text=col)
        tree.column(col, width=ancho_, anchor="w")
    tree.pack(fill="both", expand=True, padx=8, pady=(7, 4), side="top")
    for n, fila in enumerate(resultados, 1):
        (no, ambiente, rel_path, fecha_local, base_datos, stored_proc, fecha_sybase_str) = fila
        tag = ""
        if fecha_sybase_str == "No existe":
            tag = "amarillo"
        elif fecha_sybase_str == "Error":
            tag = "rosa"
        else:
            try:
                fecha_local_dt = datetime.datetime.strptime(fecha_local, "%Y-%m-%d %H:%M")
                fecha_remota = datetime.datetime.strptime(fecha_sybase_str, '%b %d %Y %I:%M%p')
                if fecha_local_dt < fecha_remota:
                    tag = "rojo"
            except Exception:
                pass
        item_id = tree.insert("", "end", values=fila, tags=(tag,))
    tree.tag_configure("rojo", background="#ef4444", foreground="white")
    tree.tag_configure("amarillo", background="#fdba74", foreground="black")
    tree.tag_configure("rosa", background="#fca5a5", foreground="white")

    def copiar_filas(event=None):
        textos = []
        for item_id in tree.selection():
            valores = tree.item(item_id)['values']
            texto = '\t'.join(str(v) for v in valores)
            textos.append(texto)
        if textos:
            win.clipboard_clear()
            win.clipboard_append('\n'.join(textos))
    tree.bind('<Control-c>', copiar_filas)
    tree.bind('<Control-C>', copiar_filas)

    def seleccionar_todos():
        for item_id in tree.get_children():
            tree.selection_add(item_id)
    def deseleccionar_todos():
        tree.selection_remove(tree.selection())

    def mover_fila(tree, direccion):
        sel = tree.selection()
        if not sel:
            return
        item = sel[0]
        items = list(tree.get_children())
        idx = items.index(item)
        if direccion == "arriba" and idx > 0:
            tree.move(item, '', idx - 1)
            tree.selection_set(item)
            tree.see(item)
        elif direccion == "abajo" and idx < len(items) - 1:
            tree.move(item, '', idx + 1)
            tree.selection_set(item)
            tree.see(item)

    def catalogar_sel_validacion():
        seleccionados = tree.selection()
        if not seleccionados:
            messagebox.showwarning("Catalogación", "Seleccione al menos un registro de esta lista.", parent=win)
            return
        for item in seleccionados:
            vals = tree.item(item)['values']
            ambiente = vals[1]
            found_ok = False
            for idx, amb in enumerate(ambientes_panel.ambientes):
                if amb['nombre'] == ambiente and ambientes_panel.estado_conex_ambs[idx] is True:
                    found_ok = True
                    break
            if not found_ok:
                messagebox.showerror(
                    "Catalogación cancelada",
                    "Uno o más ambientes de la selección han perdido la conexión OK (verde).\n"
                    "Por favor, prueba la conexión antes de catalogar.",
                    parent=win,
                )
                return
        pares_unicos = set()
        seleccionados_archs = []
        for item in seleccionados:
            vals = tree.item(item)['values']
            ambiente = vals[1]
            rel_path = vals[2]
            idx_arch = None
            for idx, arch in enumerate(archivos_unicos):
                if arch['rel_path'] == rel_path:
                    idx_arch = idx
                    break
            ambiente_obj = next((a for a in ambientes_panel.ambientes if a['nombre'] == ambiente), None)
            if idx_arch is not None and ambiente_obj is not None:
                if (idx_arch, ambiente_obj['nombre']) not in pares_unicos:
                    pares_unicos.add((idx_arch, ambiente_obj['nombre']))
                    seleccionados_archs.append((idx_arch, ambiente_obj))

        respuesta = messagebox.askyesno(
            "Confirmar catalogación",
            "¿Está seguro de catalogar los archivos seleccionados en Sybase?",
            parent=win
        )
        if respuesta:
            progreso_popup = tk.Toplevel(win)
            progreso_popup.withdraw()
            progreso_popup.title("Catalogando en Sybase...")
            progreso_popup.transient(win)
            progreso_popup.grab_set()
            lbl = ttk.Label(progreso_popup, text="0 %", font=("Segoe UI", 11), foreground="#efad00")
            lbl.pack(pady=5, padx=25)
            barra = ttk.Progressbar(progreso_popup, length=300, mode="determinate")
            barra.pack(pady=6, padx=25)

            progreso_popup.update_idletasks()
            # CENTRAR y mostrar ya correctamente formada
            ancho = progreso_popup.winfo_width()
            alto = progreso_popup.winfo_height()
            pantalla_ancho = progreso_popup.winfo_screenwidth()
            pantalla_alto = progreso_popup.winfo_screenheight()
            x = (pantalla_ancho // 2) - (ancho // 2)
            y = (pantalla_alto // 2) - (alto // 2)
            progreso_popup.geometry(f"+{x}+{y}")
            progreso_popup.deiconify()
            progreso_popup.lift()

            resultados = catalogar_archivos_multiambiente(
                archivos_unicos, seleccionados_archs, barra, lbl, progreso_popup
            )
            progreso_popup.destroy()
            messagebox.showinfo("Catálogo", "Catalogacion finalizada.")
            logear(win, f"[CATALOGACIÓN] Finalizada para {len(resultados)} archivos (ver detalles en Sybase).")
            mostrar_resumen_catalogacion(win, resultados, archivos_unicos)

    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill="x", side="bottom", pady=(5, 0), padx=10)
    btn_frame.focus_set()
    ttk.Button(btn_frame, text="Seleccionar todos", style="TButton", command=seleccionar_todos).pack(side="left", padx=2)
    ttk.Button(btn_frame, text="Quitar selección", style="TButton", command=deseleccionar_todos).pack(side="left", padx=2)
    ttk.Button(btn_frame, text="↑ Subir", style="TButton", command=lambda: mover_fila(tree, "arriba")).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="↓ Bajar", style="TButton", command=lambda: mover_fila(tree, "abajo")).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Catalogar seleccionados", style="TButton", command=catalogar_sel_validacion).pack(side="left", padx=12)
    ttk.Button(btn_frame, text="Cerrar", style="TButton", command=win.destroy).pack(side="right", padx=7)

    win.update_idletasks()
    centrar_ventana(win, ancho, alto, parent=parent)

# ------------------------
# NUEVA FUNCIÓN DE RESUMEN
# ------------------------
def mostrar_resumen_catalogacion(parent, resultados, archivos_unicos):
    win = tk.Toplevel(parent)
    win.title("Resultado Catalogacion Multiambiente")
    win.geometry("420x210")
    win.resizable(False, False)
    # Centramos la ventana
    win.update_idletasks()
    ancho = win.winfo_width()
    alto = win.winfo_height()
    pantallaw = win.winfo_screenwidth()
    pantallah = win.winfo_screenheight()
    x = (pantallaw // 2) - (ancho // 2)
    y = (pantallah // 2) - (alto // 2)
    win.geometry(f"+{x}+{y}")

    label = tk.Label(win, text="A continuación el resultado de la catalogación:", font=("Segoe UI", 14))
    label.pack(pady=25)

    btn_detalle = tk.Button(
        win, text="Ver detalle", font=("Segoe UI", 12),
        command=lambda: [win.destroy(), mostrar_resultado_catalogacion(parent, resultados, archivos_unicos)]
    )
    btn_detalle.pack(pady=10)

    btn_cerrar = tk.Button(win, text="Cerrar", font=("Segoe UI", 12), command=win.destroy)
    btn_cerrar.pack(pady=8)

    win.transient(parent)
    win.grab_set()
    win.focus_set()
    win.lift()
    return win