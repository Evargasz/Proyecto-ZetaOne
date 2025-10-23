import datetime
import logging
import pyodbc
import re
import traceback
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- CAMBIO: Mover funciones de extracción aquí para que catalogación las use ---
from ..validacion_dialog import _extraer_info_desde_encabezado, _extraer_db_de_sp, _extraer_sp_name_de_sp

# --- CAMBIO: Importar para la ventana de resultados ---
from util_ventanas import centrar_ventana


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
    # --- CORRECCIÓN: Construir la cadena de conexión con la base de datos correcta desde el inicio ---
    # Esto es más robusto que conectar a una BD por defecto y luego usar "USE".
    # Se asegura de que la sesión ODBC tenga el contexto correcto desde el principio.
    db_para_conectar = base_datos or ambiente.get('base')

    # --- CORRECCIÓN: Añadir llaves al nombre del driver para compatibilidad ---
    driver_name = ambiente.get('driver', '')

    if "SQL Server" in driver_name:
        conn_str = (
            f"Driver={{{driver_name}}};"
            f"Server={ambiente['ip']},{ambiente['puerto']};"
            f"Database={db_para_conectar};"
            f"Uid={ambiente['usuario']};"
            f"Pwd={ambiente['clave']};"
        )
    else: # Asume Sybase
        conn_str = (
            f"Driver={{{driver_name}}};"
            f"Server={ambiente['ip']};"
            f"PORT={ambiente['puerto']};"
            f"Database={db_para_conectar};"
            f"Uid={ambiente['usuario']};"
            f"Pwd={ambiente['clave']};"
        )
    try:
        # --- CAMBIO: Añadir log detallado de la conexión y los parámetros de búsqueda ---
        conn_str_log = re.sub(r'Pwd=.*?;', 'Pwd=********;', conn_str)
        # --- CORRECCIÓN: Log más claro y específico ---
        log_msg = f"[VALIDACIÓN] Buscando SP: '{stored_proc}' en BD: '{db_para_conectar}' (Ambiente: {ambiente['nombre']})"
        logging.info(log_msg)
        # --- FIN DEL CAMBIO ---

        with pyodbc.connect(conn_str, timeout=5, autocommit=True) as conn:
            cursor = conn.cursor()

            # --- SOLUCIÓN EXPERTA: Consultar sysobjects y convertir la fecha a texto en la BD ---
            # Esto evita errores de interpretación de fecha del driver ODBC y es más robusto que sp_help.
            if "SQL Server" in driver_name:
                # Para SQL Server, FORMAT es la mejor opción.
                sql = "SELECT FORMAT(crdate, 'yyyy-MM-dd HH:mm:ss') FROM sysobjects WHERE name = ? AND type = 'P'"
            else: # Asume Sybase
                # Para Sybase, CONVERT con estilo 109 es el más compatible y seguro.
                sql = "SELECT CONVERT(varchar(30), crdate, 109) FROM sysobjects WHERE name = ? AND type = 'P'"

            cursor.execute(sql, stored_proc)
            row = cursor.fetchone()
            
            if row and row[0]:
                # La fecha ya viene como una cadena de texto, lista para ser procesada en Python.
                return row[0]
            else:
                return "No encontrado en DB"

    except Exception as e:
        logging.error(f"Error en obtener_fecha_desde_sp_help: {e}")
        # --- CORRECCIÓN: Manejar el error "Object does not exist" explícitamente y relanzar otros ---
        # Si el error es que el objeto no existe, lo tratamos como un resultado válido de la validación.
        # Para otros errores (conexión, etc.), se relanza la excepción.
        error_str = str(e).lower()
        if 'object does not exist' in error_str or 'is invalid for this operation' in error_str:
            return "No encontrado en DB"
        raise e

def catalogar_plan_ejecucion(plan, descripcion, log_func):
    """
    Ejecuta el plan de catalogación, procesando cada tarea (archivo-ambiente).
    """
    resultados = []
    total_tareas = len(plan)
    log_func(f"Iniciando catalogación de {total_tareas} tareas. Descripción: '{descripcion}'")

    for i, tarea in enumerate(plan):
        archivo = tarea['archivo']
        ambiente = tarea['ambiente']
        
        log_func(f"({i+1}/{total_tareas}) Catalogando '{archivo['nombre_archivo']}' en '{ambiente['nombre']}'...")
        
        ok, msg = _catalogar_una_tarea(archivo, ambiente)
        
        resultado = {
            "ambiente": ambiente['nombre'],
            "archivo": archivo['nombre_archivo'],
            "ruta": archivo['rel_path'],
            "fecha_ejecucion": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "estado": "ÉXITO" if ok else "FALLO",
            "detalle": msg
        }
        resultados.append(resultado)
        log_func(f"  -> Resultado: {resultado['estado']} - {resultado['detalle']}")

    log_func("Proceso de catalogación finalizado.")
    return resultados

def _catalogar_una_tarea(archivo, ambiente):
    """
    Lógica para catalogar un único archivo en un único ambiente.
    """
    nombre_archivo = archivo['nombre_archivo']
    
    # 1. Determinar la base de datos y el nombre del SP/SQL
    db_desde_encabezado, sp_desde_encabezado = _extraer_info_desde_encabezado(archivo['path'])
    db_desde_use = _extraer_db_de_sp(archivo['path'])
    base_datos_a_usar = archivo.get("db_override") or db_desde_encabezado or db_desde_use or ambiente.get('base')

    sp_desde_create = _extraer_sp_name_de_sp(archivo['path'])
    nombre_sp_a_usar = archivo.get("sp_name_override") or sp_desde_encabezado or sp_desde_create or os.path.splitext(nombre_archivo)[0]

    # 2. Construir cadena de conexión
    driver_name = ambiente.get('driver', '')
    if "SQL Server" in driver_name:
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']},{ambiente['puerto']};Database={base_datos_a_usar};Uid={ambiente['usuario']};Pwd={ambiente['clave']};"
    else: # Sybase
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']};PORT={ambiente['puerto']};Database={base_datos_a_usar};Uid={ambiente['usuario']};Pwd={ambiente['clave']};"

    # 3. Ejecutar la catalogación
    try:
        with pyodbc.connect(conn_str, timeout=15, autocommit=True) as conn:
            cursor = conn.cursor()
            
            # Si es un archivo .sp, usamos sp_procxmode
            if nombre_archivo.lower().endswith('.sp'):
                sql_exec = f"sp_procxmode '{nombre_sp_a_usar}', 'anymode'"
                cursor.execute(sql_exec)
                return (True, f"Ejecutado: {sql_exec}")
            
            # Si es un archivo .sql, ejecutamos su contenido
            elif nombre_archivo.lower().endswith('.sql'):
                with open(archivo['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    sql_code = f.read()
                
                # Separar por 'go' para ejecutar en lotes
                batches = re.split(r'^\s*go\s*$', sql_code, flags=re.IGNORECASE | re.MULTILINE)
                for i, batch in enumerate(batches):
                    if batch.strip():
                        cursor.execute(batch)
                return (True, f"Script SQL ejecutado ({len(batches)} lotes)")
            
            else:
                return (False, "Tipo de archivo no soportado para catalogación")

    except Exception as e:
        return (False, f"Error: {str(e)}")

def mostrar_resultado_catalogacion(parent, resultados):
    win = tk.Toplevel(parent)
    win.title("Resultado Catalogación Multiambiente")
    win.geometry("1100x600")
    centrar_ventana(win)

    columns = ("Ambiente", "Archivo", "Ruta", "Fecha", "Estado", "Detalle")
    ancho_columnas = [120, 200, 250, 140, 80, 250]
    tree = ttk.Treeview(win, columns=columns, show="headings", height=14)
    for col, ancho_ in zip(columns, ancho_columnas):
        tree.heading(col, text=col)
        tree.column(col, width=ancho_)
    tree.pack(fill="both", expand=True, padx=18, pady=(8, 12), side="top")
    tree.tag_configure("ok", background="#bbf7d0")
    tree.tag_configure("fallido", background="#fecaca")

    for entry in resultados:
        tag = "ok" if entry['estado'] == "ÉXITO" else "fallido"
        tree.insert("", "end", values=list(entry.values()), tags=(tag,))

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
    ttk.Button(btn_frame, text="Cerrar", command=win.destroy, bootstyle="secondary").pack(side="right", padx=6)
    # TODO: Añadir funcionalidad de exportar a CSV si se requiere.