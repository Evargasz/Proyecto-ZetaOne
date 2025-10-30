import datetime
import logging
import pyodbc
import re
import traceback
import os
import tkinter as tk
from tkinter import ttk

# --- CAMBIO: Mover funciones de extracción aquí para centralizar la lógica ---
from ..validacion_dialog import _extraer_info_desde_encabezado, _extraer_db_de_sp, _extraer_sp_name_de_sp # Se mantiene por ahora para compatibilidad

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
    """
    Obtiene la fecha de creación de un SP consultando directamente sysobjects.
    Es más robusto y rápido que usar sp_help.
    """
    db_para_conectar = base_datos or ambiente.get('base')
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
        conn_str_log = re.sub(r'Pwd=.*?;', 'Pwd=********;', conn_str)
        log_msg = (
            f"[VALIDACIÓN] Buscando SP: '{stored_proc}' en BD: '{db_para_conectar}' "
            f"(Ambiente: {ambiente['nombre']}) usando sysobjects."
        )
        logging.info(log_msg)

        with pyodbc.connect(conn_str, timeout=5, autocommit=True) as conn:
            cursor = conn.cursor()

            # --- MEJORA: Consultar sysobjects y convertir la fecha a un formato estándar en la BD ---
            # Esto evita errores de parseo de fecha en Python y es más eficiente.
            if "SQL Server" in driver_name:
                # SQL Server: FORMAT es ideal para obtener 'YYYY-MM-DD HH:MI:SS'
                sql = "SELECT FORMAT(crdate, 'yyyy-MM-dd HH:mm:ss') FROM sysobjects WHERE name = ? AND type = 'P'"
            else: # Asume Sybase
                # --- CORRECCIÓN: Usar estilo 109 para máxima compatibilidad con Sybase ---
                # El estilo 120 no es soportado por todas las versiones. El 109 es más seguro.
                sql = "SELECT CONVERT(varchar(30), crdate, 109) FROM sysobjects WHERE name = ? AND type = 'P'"

            cursor.execute(sql, stored_proc)
            row = cursor.fetchone()
            
            if row and row[0]:
                # La fecha ya viene como una cadena de texto estándar, lista para ser procesada.
                return row[0]
            else:
                return "No encontrado en DB"

    except Exception as e:
        logging.error(f"Error en obtener_fecha_desde_sp_help: {e}")
        error_str = str(e).lower()
        if 'object does not exist' in error_str or 'does not exist' in error_str:
            return "No encontrado en DB"
        # Para otros errores (conexión, permisos, etc.), devolvemos un mensaje claro.
        return "Error de conexión"

def catalogar_plan_ejecucion(plan, descripcion, log_func, progress_func=None):
    """
    Ejecuta el plan de catalogación, procesando cada tarea (archivo-ambiente).
    """
    resultados = []
    
    # --- CORRECCIÓN: Aplanar el plan de ejecución antes de procesarlo ---
    # El plan puede venir en formato anidado o plano. Esta lógica lo normaliza a un formato plano.
    plan_plano = []
    for item in plan:
        if 'ambientes' in item: # Formato anidado: {"archivo": ..., "ambientes": [...]}
            for amb in item['ambientes']:
                plan_plano.append({'archivo': item['archivo'], 'ambiente': amb})
        elif 'ambiente' in item: # Formato ya plano: {"archivo": ..., "ambiente": ...}
            plan_plano.append(item)

    total_tareas = len(plan_plano)
    print(f">>> [handler] A. catalogar_plan_ejecucion INICIADO con {total_tareas} tareas.")
    log_func(f"Iniciando catalogación de {total_tareas} tareas. Descripción: '{descripcion}'")

    for i, tarea in enumerate(plan_plano):
        archivo = tarea['archivo']
        ambiente = tarea['ambiente']
        
        # --- INICIO: LÓGICA DE LA BARRA DE PROGRESO ---
        if progress_func:
            progress_func(i + 1, total_tareas, archivo['nombre_archivo'])
        # --- FIN: LÓGICA DE LA BARRA DE PROGRESO ---

        log_func(f"({i+1}/{total_tareas}) Catalogando '{archivo['nombre_archivo']}' en '{ambiente['nombre']}'...") # log_func se pasa aquí
        print(f">>> [handler] B. Procesando tarea {i+1}/{total_tareas}: '{archivo['nombre_archivo']}' en '{ambiente['nombre']}'")
        
        # --- CORRECCIÓN: Pasar log_func como argumento a la función hija ---
        ok, msg = _catalogar_una_tarea(archivo, ambiente, log_func)
        
        resultado = {
            "ambiente": ambiente['nombre'],
            "archivo": archivo['nombre_archivo'],
            "ruta": archivo.get('rel_path', 'N/A'),
            "fecha_ejecucion": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "estado": "ÉXITO" if ok else "FALLO",
            "detalle": msg
        }
        resultados.append(resultado)
        log_func(f"  -> Resultado: {resultado['estado']} - {resultado['detalle']}")

    print(">>> [handler] C. catalogar_plan_ejecucion FINALIZADO.")
    log_func("Proceso de catalogación finalizado.")
    return resultados

def _catalogar_una_tarea(archivo, ambiente, log_func):
    """
    Lógica para catalogar un único archivo en un único ambiente.
    --- CORRECCIÓN: Se añade log_func a la firma de la función ---
    """
    nombre_archivo = archivo['nombre_archivo']
    print(f">>> [handler-task] D. _catalogar_una_tarea INICIADO para '{nombre_archivo}'.")
    
    # 1. Determinar la base de datos y el nombre del SP/SQL
    db_desde_encabezado, sp_desde_encabezado = _extraer_info_desde_encabezado(archivo['path'])
    db_desde_use = _extraer_db_de_sp(archivo['path'])
    base_datos_a_usar = archivo.get("db_override") or db_desde_encabezado or db_desde_use or ambiente.get('base')

    sp_desde_create = _extraer_sp_name_de_sp(archivo['path'])
    nombre_sp_a_usar = archivo.get("sp_name_override") or sp_desde_encabezado or sp_desde_create or os.path.splitext(nombre_archivo)[0]

    print(f">>> [handler-task] E. Parámetros: DB='{base_datos_a_usar}', SP/SQL='{nombre_sp_a_usar}'.")
    # 2. Construir cadena de conexión
    driver_name = ambiente.get('driver', '')
    if "SQL Server" in driver_name:
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']},{ambiente['puerto']};Database={base_datos_a_usar};Uid={ambiente['usuario']};Pwd={ambiente['clave']};"
    else: # Sybase
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']};PORT={ambiente['puerto']};Database={base_datos_a_usar};Uid={ambiente['usuario']};Pwd={ambiente['clave']};"

    # 3. Ejecutar la catalogación
    try:
        print(f">>> [handler-task] F. Intentando conectar a la BD...")
        # --- CORRECCIÓN CRÍTICA: Usar autocommit=False y commit() explícito ---
        # Esto da control total sobre la transacción y es más robusto que confiar en autocommit=True,
        # que puede tener comportamientos inconsistentes entre drivers.
        with pyodbc.connect(conn_str, timeout=15, autocommit=False) as conn:
            # Log connection details (sensitive info masked)
            log_func(f"DEBUG: Conexión establecida para catalogación: {re.sub(r'Pwd=.*?;', 'Pwd=********;', conn_str)}")
            log_func(f"DEBUG: Intentando catalogar archivo: {nombre_archivo} (SP/SQL: {nombre_sp_a_usar}, DB: {base_datos_a_usar})")
            
            cursor = conn.cursor()
            
            # --- CORRECCIÓN: Para archivos .sp, ejecutar su contenido para actualizar crdate ---
            # Si el objetivo es que la fecha de creación/modificación (crdate) se actualice,
            # es necesario ejecutar el contenido del archivo .sp (que contiene CREATE/ALTER PROCEDURE).
            # sp_procxmode es una operación administrativa que no afecta la crdate.
            if nombre_archivo.lower().endswith('.sp'):
                with open(archivo['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    sp_code = f.read()
                
                # Asegurar el contexto de la base de datos para el script SP
                sp_code_con_contexto = f"USE {base_datos_a_usar}\nGO\n{sp_code}"
                
                print(f">>> [handler-task] G. Leyendo script SP: {archivo['path']}")
                log_func(f"DEBUG: Leyendo y preparando SP para DB '{base_datos_a_usar}'")
                
                # Separar por 'go' para ejecutar en lotes
                batches = re.split(r'^\s*go\s*$', sp_code_con_contexto, flags=re.IGNORECASE | re.MULTILINE)
                for i, batch in enumerate(batches):
                    if batch.strip():
                        print(f">>> [handler-task] H. Ejecutando batch {i+1}/{len(batches)} (SP)...")
                        log_func(f"DEBUG: Ejecutando batch {i+1}/{len(batches)} para {nombre_archivo}:\n{batch.strip()[:200]}...")
                        cursor.execute(batch)
                conn.commit() # Confirmar la transacción para el despliegue del SP
                return (True, f"Stored Procedure '{nombre_sp_a_usar}' desplegado ({len(batches)} lotes)")
            
            # Si es un archivo .sql, ejecutamos su contenido
            elif nombre_archivo.lower().endswith('.sql'):
                with open(archivo['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    sql_code = f.read()
                
                # --- CORRECCIÓN CRÍTICA: Asegurar el contexto de la base de datos para scripts SQL ---
                # Se antepone 'USE [database]' al script para garantizar que se ejecute en la BD correcta.
                # Esto es vital si el script no incluye su propio comando USE.
                sql_code_con_contexto = f"USE {base_datos_a_usar}\nGO\n{sql_code}"
                
                print(f">>> [handler-task] G. Leyendo script SQL: {archivo['path']}")
                log_func(f"DEBUG: Leyendo y preparando script SQL para DB '{base_datos_a_usar}'")
                
                # Separar por 'go' para ejecutar en lotes
                batches = re.split(r'^\s*go\s*$', sql_code_con_contexto, flags=re.IGNORECASE | re.MULTILINE)
                for i, batch in enumerate(batches):
                    if batch.strip():
                        # La primera ejecución será el "USE [database]"
                        print(f">>> [handler-task] H. Ejecutando batch {i+1}/{len(batches)}...")
                        log_func(f"DEBUG: Ejecutando batch {i+1}/{len(batches)} para {nombre_archivo}:\n{batch.strip()[:200]}...") # Log first 200 chars
                        cursor.execute(batch)
                
                conn.commit() # Confirmar la transacción para el archivo SQL
                return (True, f"Script SQL ejecutado ({len(batches)} lotes)")
            
            else:
                log_func(f"ADVERTENCIA: Tipo de archivo no soportado para catalogación: {nombre_archivo}")
                return (False, "Tipo de archivo no soportado para catalogación")

    except Exception as e:
        # No es necesario un conn.rollback() aquí porque el 'with' se encarga de cerrar
        # la conexión sin hacer commit si ocurre una excepción.
        print(f">>> [handler-task] I. ERROR en _catalogar_una_tarea: {e}\n{traceback.format_exc()}")
        error_detail = f"Error durante la catalogación de '{nombre_archivo}' en '{ambiente['nombre']}': {str(e)}"
        log_func(f"ERROR: {error_detail}\n{traceback.format_exc()}") # Log full traceback to the UI log
        return (False, f"Error: {str(e)}")

def mostrar_resultado_catalogacion(parent, resultados):
    win = tk.Toplevel(parent)
    win.title("Resultado Catalogación Multiambiente")
    win.geometry("1100x600")
    centrar_ventana(win)
    # --- CAMBIO: Hacer la ventana modal para que bloquee hasta que se cierre ---
    win.transient(parent)
    win.grab_set()
    # --- FIN DEL CAMBIO ---

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

    # --- CAMBIO: Esperar a que la ventana de resultados se cierre ---
    parent.wait_window(win)