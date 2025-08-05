import datetime
import logging
import pyodbc
import re
import traceback
import os
import csv
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

def validar_archivo_sp_local_vs_sybase(arch, ambiente, stored_proc, base_datos):
    try:
        logging.info(f"DEBUG: Consultando en Sybase/SQLServer con SP: {stored_proc!r} y base: {base_datos!r}")
        print(f"DEBUG: Consultando en Sybase/SQLServer con SP: {stored_proc!r} y base: {base_datos!r}")

        fecha_sybase_str = obtener_fecha_desde_sp_help(stored_proc, base_datos, ambiente)
        print("DEBUG: Fecha devuelta por DB remota:", fecha_sybase_str)
        logging.info(f"DEBUG: Fecha devuelta por DB remota: {fecha_sybase_str}")
        fecha_sybase = None
        if fecha_sybase_str and fecha_sybase_str.strip() and fecha_sybase_str != "No existe":
            try:
                fecha_sybase = datetime.datetime.strptime(fecha_sybase_str.strip(), '%b %d %Y %I:%M%p')
            except Exception as e:
                logging.warning(f"Error al parsear fecha DB remota: {fecha_sybase_str} ==> {str(e)}")
                fecha_sybase = None
        else:
            fecha_sybase = None
        return (fecha_sybase_str, fecha_sybase)
    except Exception as e:
        logging.error(f"Error en validar_archivo_sp_local_vs_sybase: {e}")
        return ("Error", None)

def obtener_fecha_desde_sp_help(stored_proc, base_datos, ambiente):
    if "SQL Server" in ambiente['driver']:
        conn_str = (
            f"Driver={ambiente['driver']};"
            f"Server={ambiente['ip']},{ambiente['puerto']};"
            f"Database={base_datos};"
            f"Uid={ambiente['usuario']};"
            f"Pwd={ambiente['clave']};"
        )
    else:
        conn_str = (
            f"Driver={ambiente['driver']};"
            f"Server={ambiente['ip']};"
            f"PORT={ambiente['puerto']};"
            f"Database={base_datos};"
            f"Uid={ambiente['usuario']};"
            f"Pwd={ambiente['clave']};"
        )
    try:
        with pyodbc.connect(conn_str, timeout=5, autocommit=True) as conn:
            cursor = conn.cursor()
            sql = f"sp_help {stored_proc}"
            logging.info(f"[DEBUG SQL] Ejecutando: {sql}")
            cursor.execute(sql)
            while True:
                columns = [column[0] for column in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    if 'Create_date' in row_dict and row_dict['Create_date']:
                        value = row_dict['Create_date']
                        if isinstance(value, datetime.datetime):
                            return value.strftime('%b %d %Y %I:%M%p')
                        else:
                            return str(value)
                if not cursor.nextset():
                    break
            return "No existe"
    except Exception as e:
        logging.error(f"Error accediendo a BD/sp_help: {e}")
        return "No existe"

def catalogar_archivo_en_ambiente(path, ambiente):
    try:
        try:
            try:
                with open(path, encoding="utf-8") as f:
                    sql_code = f.read()
            except UnicodeDecodeError:
                with open(path, encoding="latin1") as f:
                    sql_code = f.read()
        except Exception as e:
            return (False, f"Error leyendo el archivo: {e}")

        if "SQL Server" in ambiente['driver']:
            conn_str = (
                f"Driver={ambiente['driver']};"
                f"Server={ambiente['ip']},{ambiente['puerto']};"
                f"Database={ambiente['base']};"
                f"Uid={ambiente['usuario']};"
                f"Pwd={ambiente['clave']};"
            )
        else:
            conn_str = (
                f"Driver={ambiente['driver']};"
                f"Server={ambiente['ip']};"
                f"PORT={ambiente['puerto']};"
                f"Database={ambiente['base']};"
                f"Uid={ambiente['usuario']};"
                f"Pwd={ambiente['clave']};"
            )

        with pyodbc.connect(conn_str, timeout=30, autocommit=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SET CHAINED OFF")
            except Exception as e:
                logging.warning("SET CHAINED OFF falló: %s", str(e))
            try:
                cursor.execute("SET NOCOUNT ON")
            except Exception as e:
                logging.warning("SET NOCOUNT ON falló: %s", str(e))
            batches = re.split(r'(?im)^[ \t]*go[ \t]*$', sql_code, flags=re.MULTILINE)
            for idx, batch in enumerate(batches):
                stmt = batch.strip()
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        conn.rollback()
                        return (False, f"Error ejecutando batch #{idx+1}: {e}\nBatch SQL:\n{stmt}\nTrace:\n{traceback.format_exc()}")
            return (True, "Catalogado OK (ejecutado en Base de Datos)")
    except Exception as e:
        return (False, f"Error ejecutando en la Base de Datos: {e}\n{traceback.format_exc()}")

def catalogar_archivos_multiambiente(archivos_unicos, pares_idx_amb, progress, lbl_porc, progreso_win):
    resultados = []
    contador = 0
    total = len(pares_idx_amb)
    for idx, amb in pares_idx_amb:
        arch = archivos_unicos[idx]
        ok, msg = catalogar_archivo_en_ambiente(arch['path'], amb)
        resultado = "OK" if ok else "Fallida"
        fila = (
            amb['nombre'],
            arch['nombre_archivo'],
            arch['rel_path'],
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            resultado,
            msg
        )
        resultados.append(fila)
        contador += 1
        porc = int((contador / total) * 100) if total > 0 else 100
        progress['value'] = contador
        lbl_porc.config(text=f"{porc} %")
        progreso_win.update_idletasks()
    return resultados

def mostrar_resultado_catalogacion(parent, resultados, archivos_unicos):
    win = tk.Toplevel(parent)
    win.title("Resultado Catalogación Multiambiente")
    ancho_total = 1000
    alto_total = 480
    win.geometry(f"{ancho_total}x{alto_total}")
    win.update_idletasks()
    # >>>>>> CENTRA LA VENTANA <<<<<<
    ancho = win.winfo_width()
    alto = win.winfo_height()
    pantalla_ancho = win.winfo_screenwidth()
    pantalla_alto = win.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho // 2)
    y = (pantalla_alto // 2) - (alto // 2)
    win.geometry(f"{ancho_total}x{alto_total}+{x}+{y}")
    # >>>>>> FIN CENTRADO <<<<<<

    def guardar_en_carpeta_catalogaciones():
        now = datetime.datetime.now()
        nombre = now.strftime("%Y%m%d%H%M")
        base_dir = r"C:\ZetaOne\Catalogaciones"
        carpeta_destino = os.path.join(base_dir, nombre)
        try:
            os.makedirs(carpeta_destino, exist_ok=True)
        except Exception:
            return
        exitosos = [entry for entry in resultados if entry[4] == "OK"]
        for entry in exitosos:
            archivo_encontrado = next(
                (a for a in archivos_unicos if a["nombre_archivo"] == entry[1]), None)
            if archivo_encontrado and os.path.exists(archivo_encontrado["path"]):
                try:
                    destino = os.path.join(
                        carpeta_destino,
                        os.path.basename(archivo_encontrado["nombre_archivo"]) + ".txt"
                    )
                    with open(archivo_encontrado["path"], "r", encoding="utf-8", errors="ignore") as f_in, \
                         open(destino, "w", encoding="utf-8") as f_out:
                        f_out.write(f_in.read())
                except Exception:
                    pass

        resumen_path = os.path.join(carpeta_destino, "catalogacion_exitosa.txt")
        with open(resumen_path, "w", encoding="utf-8") as resumen:
            resumen.write("ARCHIVOS CATALOGADOS EXITOSAMENTE\n\n")
            for entry in exitosos:
                resumen.write(f"Archivo: {entry[1]}\n")
                resumen.write(f"Ruta: {entry[2]}\n")
                resumen.write(f"Ambiente: {entry[0]}\n")
                resumen.write(f"Fecha: {entry[3]}\n")
                resumen.write("-" * 60 + "\n")

        csv_path = os.path.join(carpeta_destino, "catalogacion_exitosa.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Archivo", "Ruta", "Ambiente", "Fecha"])
            for entry in exitosos:
                writer.writerow([entry[1], entry[2], entry[0], entry[3]])

        fallidos = [entry for entry in resultados if entry[4] == "Fallida"]
        if fallidos:
            carpeta_fallidos = os.path.join(carpeta_destino, "fallidos")
            os.makedirs(carpeta_fallidos, exist_ok=True)
            csv_fallidos_path = os.path.join(carpeta_fallidos, "fallidos_catalogacion.csv")
            with open(csv_fallidos_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Archivo", "Ruta Original", "Ambiente", "Fecha", "Mensaje Base/Error"])
                for entry in fallidos:
                    archivo_encontrado = next(
                        (a for a in archivos_unicos if a["nombre_archivo"] == entry[1]), None)
                    if archivo_encontrado and os.path.exists(archivo_encontrado["path"]):
                        try:
                            destino = os.path.join(carpeta_fallidos, os.path.basename(archivo_encontrado["nombre_archivo"]))
                            shutil.copy2(archivo_encontrado["path"], destino)
                            ruta_original = archivo_encontrado["path"]
                        except Exception as e:
                            ruta_original = f"Error al copiar: {str(e)}"
                    else:
                        ruta_original = "(No encontrado)"
                    writer.writerow([entry[1], ruta_original, entry[0], entry[3], entry[5]])
        return "OK"
    guardar_en_carpeta_catalogaciones()

    columns = ("Ambiente", "Archivo", "Ruta", "Fecha", "Estado", "Detalle/Error")
    ancho_columnas = [120, 210, 240, 120, 98, 255]
    tree = ttk.Treeview(win, columns=columns, show="headings", height=14)
    for col, ancho_ in zip(columns, ancho_columnas):
        tree.heading(col, text=col)
        tree.column(col, width=ancho_)
    tree.pack(fill="both", expand=True, padx=18, pady=(8, 12), side="top")
    tree.tag_configure("ok", background="#bbf7d0")
    tree.tag_configure("fallido", background="#fecaca")
    for entry in resultados:
        tag = "ok" if entry[4] == "OK" else "fallido"
        tree.insert("", "end", values=entry, tags=(tag,))

    def copiar_filas(event=None):
        items = tree.selection()
        if not items:
            return
        registros = []
        for iid in items:
            valores = tree.item(iid, "values")
            registros.append('\t'.join(str(val) for val in valores))
        if registros:
            win.clipboard_clear()
            win.clipboard_append('\n'.join(registros))
    tree.bind('<Control-c>', copiar_filas)
    tree.bind('<Control-C>', copiar_filas)

    btn_frame = tk.Frame(win)
    btn_frame.pack(fill="x", side="bottom", pady=(1, 7), padx=16)
    ttk.Button(btn_frame, text="Cerrar", command=win.destroy).pack(side="right", padx=6)
    ttk.Button(btn_frame, text="Exportar CSV", command=lambda: exportar_csv(tree)).pack(side="right", padx=7)

    def exportar_csv(treeview):
        fichero = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            title="Guardar como CSV"
        )
        if not fichero:
            return
        datos = [treeview.item(iid, "values") for iid in treeview.get_children()]
        try:
            with open(fichero, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(datos)
            messagebox.showinfo("Exportado", f"Archivo guardado:\n{fichero}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el CSV:\n{e}")

    win.update_idletasks()
    # Vuelve a asegurar el centrado después de cualquier ajuste de tamaño
    ancho, alto = win.winfo_width(), win.winfo_height()
    pantalla_ancho = win.winfo_screenwidth()
    pantalla_alto = win.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho // 2)
    y = (pantalla_alto // 2) - (alto // 2)
    win.geometry(f"{ancho}x{alto}+{x}+{y}")