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

# ============================================================================
# Función para extraer comentarios iniciales del archivo
# ============================================================================

def extraer_comentarios_iniciales(ruta_archivo):
    """
    Extrae los comentarios y líneas iniciales del archivo antes del código compilado.
    Se detiene cuando encuentra CREATE, ALTER, o comandos SQL principales.
    
    Returns:
        str: Los comentarios/encabezado iniciales del archivo
    """
    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            lineas_iniciales = []
            for linea in f:
                linea_strip = linea.strip()
                linea_upper = linea_strip.upper()
                
                # Detener cuando encontremos el comentario @last-modified-date (este queda compilado)
                if linea_strip.startswith('--') and '@LAST-MODIFIED-DATE' in linea_upper:
                    break
                
                # Detener cuando encontremos el inicio del código compilado
                if (linea_upper.startswith('CREATE ') or 
                    linea_upper.startswith('ALTER ') or
                    linea_upper.startswith('EXEC ') or
                    linea_upper.startswith('EXECUTE ')):
                    break
                
                # Incluir comentarios y líneas vacías
                lineas_iniciales.append(linea.rstrip('\n'))
            
            return '\n'.join(lineas_iniciales) if lineas_iniciales else ""
    except Exception as e:
        print(f">>> ERROR extrayendo comentarios iniciales: {e}")
        return ""

# ============================================================================
# Función auxiliar para procesar código nuevo
# ============================================================================

def _eliminar_encabezado_hasta_last_modified(codigo_fuente):
    """
    Elimina todo el encabezado del archivo hasta encontrar (e incluir) la línea @last-modified-date.
    El archivo resultante empieza con --@last-modified-date seguido del código compilado.
    
    Args:
        codigo_fuente: Código fuente completo del archivo
    
    Returns:
        str: Código sin encabezado, empezando con @last-modified-date
    """
    if not codigo_fuente:
        return codigo_fuente
    
    try:
        lineas = codigo_fuente.split('\n')
        lineas_resultado = []
        encontrado_last_modified = False
        
        for linea in lineas:
            linea_strip = linea.strip()
            linea_upper = linea_strip.upper()
            
            # Buscar la línea @last-modified-date
            if not encontrado_last_modified and linea_strip.startswith('--') and '@LAST-MODIFIED-DATE' in linea_upper:
                encontrado_last_modified = True
                lineas_resultado.append(linea)  # Incluir esta línea
                continue
            
            # Una vez encontrado, incluir todas las líneas siguientes
            if encontrado_last_modified:
                lineas_resultado.append(linea)
        
        # Si no se encontró @last-modified-date, devolver el código original
        if not encontrado_last_modified:
            return codigo_fuente
        
        return '\n'.join(lineas_resultado)
    
    except Exception as e:
        print(f">>> ERROR eliminando encabezado: {e}")
        return codigo_fuente  # En caso de error, devolver original

# ============================================================================
# RF-CATALOG-RESPALDO-001: Funciones de respaldo de fuentes
# ============================================================================

def extraer_codigo_fuente_db(nombre_objeto, base_datos, ambiente, log_func=None):
    """
    Extrae el código fuente de un objeto (SP, trigger, etc.) desde la base de datos.
    
    Args:
        nombre_objeto: Nombre del objeto (puede incluir esquema)
        base_datos: Base de datos a consultar
        ambiente: Dict con datos de conexión
        log_func: Función de logging opcional
    
    Returns:
        Tuple[bool, str]: (éxito, código_fuente o mensaje_error)
    """
    driver_name = ambiente.get('driver', '')
    
    if "SQL Server" in driver_name:
        conn_str = (
            f"Driver={{{driver_name}}};"
            f"Server={ambiente['ip']},{ambiente['puerto']};"
            f"Database={base_datos};"
            f"Uid={ambiente['usuario']};"
            f"Pwd={ambiente['clave']};"
        )
    else:  # Sybase
        conn_str = (
            f"Driver={{{driver_name}}};"
            f"Server={ambiente['ip']};"
            f"PORT={ambiente['puerto']};"
            f"Database={base_datos};"
            f"Uid={ambiente['usuario']};"
            f"Pwd={ambiente['clave']};"
        )
    
    try:
        with pyodbc.connect(conn_str, timeout=10, autocommit=True) as conn:
            cursor = conn.cursor()
            
            # Determinar el comando según el tipo de BD
            driver_name = ambiente.get('driver', '')
            if "SQL Server" in driver_name:
                comando = f"sp_helptext '{nombre_objeto}'"
                print(f">>> [extract] DEBUG: Ejecutando comando SQL Server: {comando}")
                cursor.execute(comando)
                
                lineas = []
                row_count = 0
                for row in cursor.fetchall():
                    row_count += 1
                    if row and len(row) > 0:
                        texto = str(row[0]) if row[0] else ""
                        if texto:
                            lineas.append(texto)
                
            else:  # Sybase - consultar syscomments directamente
                comando = f"""
                SELECT text 
                FROM syscomments 
                WHERE id = object_id('{nombre_objeto}')
                ORDER BY colid
                """
                print(f">>> [extract] DEBUG: Ejecutando query Sybase a syscomments")
                
                lineas = []
                row_count = 0
                
                cursor.execute(comando)
                rows = cursor.fetchall()
                for row in rows:
                    row_count += 1
                    if row and len(row) > 0:
                        texto = str(row[0]) if row[0] else ""
                        if texto:
                            lineas.append(texto)
                            if row_count <= 3:
                                print(f">>> [extract] DEBUG: Fila {row_count}: '{texto[:50]}...' (longitud: {len(texto)})")
            
            print(f">>> [extract] DEBUG: Total de filas procesadas: {row_count}, fragmentos con contenido: {len(lineas)}")
            
            if not lineas:
                return (False, "OBJECT NOT FOUND")
            
            # Unir sin agregar separador adicional
            codigo_completo = ''.join(lineas)
            
            # Debug: verificar longitud
            if log_func:
                log_func(f"DEBUG: sp_helptext retornó {len(lineas)} fragmentos, total {len(codigo_completo)} caracteres")
            
            return (True, codigo_completo)
            
    except Exception as e:
        error_msg = str(e)
        if log_func:
            log_func(f"ERROR extrayendo código de '{nombre_objeto}': {error_msg}")
        logging.error(f"Error en extraer_codigo_fuente_db: {error_msg}")
        return (False, error_msg)


def generar_archivo_respaldo(codigo_fuente, nombre_base, tipo_archivo, ambiente, carpeta_destino, metadatos=None, log_func=None, comentarios_iniciales=None, extension_original=None, ruta_archivo_original=None):
    """
    Genera un archivo de respaldo con el código fuente extraído.
    
    Args:
        codigo_fuente: Código fuente del objeto
        nombre_base: Nombre base del archivo (sin extensión)
        tipo_archivo: 'respaldo' o 'nuevo'
        ambiente: Dict con datos del ambiente
        carpeta_destino: Carpeta donde guardar el archivo
        metadatos: Dict opcional con metadata adicional
        log_func: Función de logging opcional
        comentarios_iniciales: Comentarios/encabezado del archivo original (opcional)
        extension_original: Extensión original del archivo fuente (ej: 'sp', 'sql', 'tq')
        ruta_archivo_original: Ruta completa del archivo original (opcional)
    
    Returns:
        Tuple[bool, str]: (éxito, path_archivo o mensaje_error)
    """
    try:
        # Determinar extensión: usar la original si se proporciona, sino determinar por tipo de BD
        if extension_original:
            extension = extension_original.lstrip('.')  # Quitar el punto si viene con él
        else:
            # Fallback: determinar por tipo de BD (compatibilidad con código antiguo)
            driver_name = ambiente.get('driver', '')
            if "SQL Server" in driver_name:
                extension = 'tq'
            else:
                extension = 'sp'
        
        # Determinar tipo de BD para el encabezado
        driver_name = ambiente.get('driver', '')
        if "SQL Server" in driver_name:
            db_type = 'SQLServer'
        else:
            db_type = 'Sybase'
        
        # Generar timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Construir nombre de archivo
        nombre_archivo = f"{nombre_base}_{tipo_archivo}_{timestamp}.{extension}"
        path_completo = os.path.join(carpeta_destino, nombre_archivo)
        
        # Construir nombre con extensión para SOURCE-NAME
        nombre_con_extension = f"{nombre_base}.{extension}"
        
        # Construir cabecera con metadatos
        cabecera = [
            f"-- SOURCE-NAME: {nombre_con_extension}",
            f"-- SOURCE-PATH: {ruta_archivo_original if ruta_archivo_original else 'N/A'}",
            f"-- DB-TYPE: {db_type}",
            f"-- HOST: {ambiente.get('ip', 'N/A')}",
            f"-- DATABASE: {metadatos.get('base_datos', 'N/A') if metadatos else 'N/A'}",
            f"-- GENERATED-BY: ZetaOne-Catalogacion",
            f"-- GENERATED-AT: {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
            f"-- NOTE: {tipo_archivo}",
            "-- " + "="*70,
            ""
        ]
        
        # Escribir archivo
        with open(path_completo, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cabecera))
            f.write('\n')  # Línea en blanco entre cabecera y código
            
            # Procesar el código según el tipo de archivo
            # AMBOS archivos (nuevo y respaldo) deben empezar con @last-modified-date
            codigo_procesado = _eliminar_encabezado_hasta_last_modified(codigo_fuente)
            f.write(codigo_procesado if codigo_procesado else "-- NO CONTENT AVAILABLE --")
            
            # Agregar go final si no está presente
            if codigo_fuente and not codigo_fuente.strip().upper().endswith('GO'):
                f.write('\ngo\n')
        
        if log_func:
            log_func(f"✅ Respaldo generado: {nombre_archivo} ({len(codigo_fuente) if codigo_fuente else 0} caracteres)")
        logging.info(f"Respaldo generado: {path_completo}")
        
        return (True, path_completo)
        
    except Exception as e:
        error_msg = f"Error generando archivo de respaldo: {str(e)}"
        if log_func:
            log_func(f"❌ {error_msg}")
        logging.error(error_msg)
        return (False, error_msg)


def validar_archivo_sp_local_vs_sybase(arch, ambiente, stored_proc, base_datos):
    try:
        logging.info(f"DEBUG: Consultando en Sybase/SQLServer con SP: {stored_proc!r} y base: {base_datos!r}")
        print(f"DEBUG: Consultando en Sybase/SQLServer con SP: {stored_proc!r} y base: {base_datos!r}")

        resultado = obtener_fecha_desde_sp_help(stored_proc, base_datos, ambiente)
        # Ahora resultado es una tupla (fecha_str, bd_real)
        fecha_sybase_str, bd_real = resultado
        
        print("DEBUG: Fecha devuelta por DB remota:", fecha_sybase_str)
        if bd_real:
            print(f"DEBUG: ⚠️ BD REAL donde se encontró: '{bd_real}' (diferente a la del archivo: '{base_datos}')")
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
        
        # Retornar también la BD real
        return (fecha_sybase_str, fecha_sybase, bd_real)
    except Exception as e:
        logging.error(f"Error en validar_archivo_sp_local_vs_sybase: {e}")
        return ("Error", None, None)

def obtener_fecha_desde_sp_help(stored_proc, base_datos, ambiente, progress_callback=None):
    """
    Obtiene la fecha de creación de un SP consultando directamente sysobjects.
    Si no lo encuentra en la BD especificada, busca en todas las BDs del servidor.
    
    Args:
        progress_callback: Función opcional que se llama con (bd_actual) para reportar progreso
    
    Retorna: tupla (fecha, bd_real) o (fecha, None) si se encontró en la BD original, o ("No encontrado en DB", None)
    """
    # --- CORRECCIÓN: Validar el case de la base de datos antes de usarla ---
    db_inicial = base_datos or ambiente.get('base')
    
    # Validar la BD con la función de corrección de case
    try:
        db_para_conectar = _validar_y_corregir_base_datos_para_validacion(db_inicial, ambiente)
    except:
        db_para_conectar = db_inicial
    # --- FIN CORRECCIÓN ---
    
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
            f"(Ambiente: {ambiente['nombre']}) usando sysobjects. "
            f"BD original: '{db_inicial}'"
        )
        logging.info(log_msg)
        print(f"DEBUG: {log_msg}")  # Para depuración en consola

        with pyodbc.connect(conn_str, timeout=5, autocommit=True) as conn:
            cursor = conn.cursor()

            # --- CORRECCIÓN: Búsqueda case-insensitive para el nombre del SP ---
            # En Sybase, los nombres de objetos pueden ser case-sensitive dependiendo de la configuración
            if "SQL Server" in driver_name:
                # SQL Server: FORMAT es ideal para obtener 'YYYY-MM-DD HH:MI:SS'
                sql = "SELECT FORMAT(crdate, 'yyyy-MM-dd HH:mm:ss') FROM sysobjects WHERE LOWER(name) = LOWER(?) AND type = 'P'"
            else: # Asume Sybase
                # Búsqueda case-insensitive con LOWER() y formato de fecha compatible
                sql = "SELECT CONVERT(varchar(30), crdate, 109) FROM sysobjects WHERE LOWER(name) = LOWER(?) AND type = 'P'"
            
            print(f"DEBUG: Ejecutando SQL: {sql} con parámetro: '{stored_proc}'")
            cursor.execute(sql, stored_proc)
            row = cursor.fetchone()
            
            if row and row[0]:
                # SP encontrado en la BD especificada
                print(f"DEBUG: ✅ SP encontrado en '{db_para_conectar}', fecha: {row[0]}")
                return (row[0], None)  # None indica que se usó la BD original
            else:
                print(f"DEBUG: ⚠️ SP NO encontrado en '{db_para_conectar}'")
                
                # --- VERIFICAR SI LA BD PARECE MAL ESCRITA ---
                # Solo hacer búsqueda inteligente si:
                # 1. El nombre tiene espacios (ej: "COBIS WORKFLOW")
                # 2. No empieza con "cob_" (podría estar mal)
                # 3. Tiene palabras en mayúsculas mezcladas
                bd_parece_incorrecta = (
                    ' ' in db_para_conectar or  # Tiene espacios
                    (not db_para_conectar.lower().startswith('cob_') and len(db_para_conectar.split()) == 1)  # No tiene cob_ y es palabra única
                )
                
                if not bd_parece_incorrecta:
                    # La BD parece correcta pero el SP no está ahí - retornar directamente
                    print(f"DEBUG: BD '{db_para_conectar}' parece correcta. SP simplemente no existe.")
                    return ("No encontrado en DB", None)
                
                print(f"DEBUG: ⚠️ BD '{db_para_conectar}' parece incorrecta. Iniciando búsqueda inteligente...")
                
                # --- BÚSQUEDA INTELIGENTE con combinaciones de palabras ---
                # Extraer palabras del nombre de la BD
                palabras = db_para_conectar.replace('_', ' ').split()
                palabras = [p.lower() for p in palabras if p.lower() not in ['cob', '']]
                
                print(f"DEBUG: Palabras extraídas de la BD: {palabras}")
                
                # Generar combinaciones inteligentes con prefijo "cob_"
                combinaciones_a_probar = []
                
                # 1. Cada palabra individual con prefijo cob_
                for palabra in palabras:
                    combinacion = f"cob_{palabra}"
                    if combinacion not in combinaciones_a_probar:
                        combinaciones_a_probar.append(combinacion)
                
                # 2. Combinación de todas las palabras con prefijo cob_
                if len(palabras) > 1:
                    combinacion_completa = f"cob_{'_'.join(palabras)}"
                    if combinacion_completa not in combinaciones_a_probar:
                        combinaciones_a_probar.append(combinacion_completa)
                
                # 3. Si solo hay una palabra y no empieza con "cob_", agregar también la versión sin prefijo
                if len(palabras) == 1 and not db_para_conectar.lower().startswith('cob_'):
                    if palabras[0] not in combinaciones_a_probar:
                        combinaciones_a_probar.append(palabras[0])
                
                print(f"DEBUG: Combinaciones a probar: {combinaciones_a_probar}\n")
                
                # Intentar con cada combinación
                for idx, bd_candidata in enumerate(combinaciones_a_probar, 1):
                    # Notificar progreso a la UI si hay callback
                    if progress_callback:
                        progress_callback(bd_candidata)
                    
                    print(f"[Intento {idx}/{len(combinaciones_a_probar)}] Probando BD: '{bd_candidata}'...", end=" ")
                    
                    try:
                        # Validar si existe esta BD
                        bd_validada = _validar_y_corregir_base_datos_para_validacion(bd_candidata, ambiente)
                        
                        # Si retorna algo diferente, verificar si realmente existe
                        if "SQL Server" in driver_name:
                            conn_str_test = (
                                f"Driver={{{driver_name}}};"
                                f"Server={ambiente['ip']},{ambiente['puerto']};"
                                f"Database={bd_validada};"
                                f"Uid={ambiente['usuario']};"
                                f"Pwd={ambiente['clave']};"
                            )
                        else:
                            conn_str_test = (
                                f"Driver={{{driver_name}}};"
                                f"Server={ambiente['ip']};"
                                f"PORT={ambiente['puerto']};"
                                f"Database={bd_validada};"
                                f"Uid={ambiente['usuario']};"
                                f"Pwd={ambiente['clave']};"
                            )
                        
                        # Intentar conectar y buscar el SP
                        with pyodbc.connect(conn_str_test, timeout=5, autocommit=True) as conn_test:
                            cursor_test = conn_test.cursor()
                            
                            if "SQL Server" in driver_name:
                                sql_test = "SELECT FORMAT(crdate, 'yyyy-MM-dd HH:mm:ss') FROM sysobjects WHERE LOWER(name) = LOWER(?) AND type = 'P'"
                            else:
                                sql_test = "SELECT CONVERT(varchar(30), crdate, 109) FROM sysobjects WHERE LOWER(name) = LOWER(?) AND type = 'P'"
                            
                            cursor_test.execute(sql_test, stored_proc)
                            row_test = cursor_test.fetchone()
                            
                            if row_test and row_test[0]:
                                print(f"✅ ENCONTRADO!")
                                print(f"\n{'='*70}")
                                print(f"ℹ️  ATENCIÓN: BD en archivo '{db_para_conectar}' es incorrecta")
                                print(f"ℹ️  SP encontrado en BD real: '{bd_validada}'")
                                print(f"{'='*70}\n")
                                # Retornar tupla (fecha, bd_real)
                                return (row_test[0], bd_validada)
                            else:
                                print(f"BD existe pero SP no está ahí")
                    except Exception as e_comb:
                        print(f"BD no existe o error: {str(e_comb)[:50]}")
                        continue
                
                print(f"\nDEBUG: SP no encontrado en ninguna combinación inteligente")
                
                # --- TERCER INTENTO: Buscar en todas las bases de datos ---
                print(f"\n{'='*70}")
                print(f"🔍 BUSCANDO SP '{stored_proc}' EN TODAS LAS BD DEL SERVIDOR...")
                print(f"{'='*70}\n")
                try:
                    # Primero obtener lista de todas las BDs conectándose a master
                    if "SQL Server" in driver_name:
                        cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
                    else:  # Sybase - especificar owner para sysdatabases
                        cursor.execute("SELECT name FROM master.dbo.sysdatabases WHERE name NOT IN ('master', 'tempdb', 'model', 'sybsystemprocs', 'sybsystemdb')")
                    
                    todas_bds = [row[0] for row in cursor.fetchall()]
                    print(f"DEBUG: Total de {len(todas_bds)} bases de datos a revisar")
                    print(f"DEBUG: Lista completa: {todas_bds}\n")
                    
                    # Buscar el SP en cada BD creando una conexión específica
                    for idx, bd_nombre in enumerate(todas_bds, 1):
                        # Notificar progreso a la UI si hay callback
                        if progress_callback:
                            progress_callback(bd_nombre)
                        
                        print(f"[{idx}/{len(todas_bds)}] Buscando en BD: '{bd_nombre}'...", end=" ")
                        try:
                            # Crear conexión directa a esta BD específica
                            if "SQL Server" in driver_name:
                                conn_str_bd = (
                                    f"Driver={{{driver_name}}};"
                                    f"Server={ambiente['ip']},{ambiente['puerto']};"
                                    f"Database={bd_nombre};"
                                    f"Uid={ambiente['usuario']};"
                                    f"Pwd={ambiente['clave']};"
                                )
                            else:  # Sybase
                                conn_str_bd = (
                                    f"Driver={{{driver_name}}};"
                                    f"Server={ambiente['ip']};"
                                    f"PORT={ambiente['puerto']};"
                                    f"Database={bd_nombre};"
                                    f"Uid={ambiente['usuario']};"
                                    f"Pwd={ambiente['clave']};"
                                )
                            
                            # Conectar a esta BD específica
                            with pyodbc.connect(conn_str_bd, timeout=3, autocommit=True) as conn_bd:
                                cursor_bd = conn_bd.cursor()
                                
                                # Buscar el SP en esta BD
                                if "SQL Server" in driver_name:
                                    sql_busqueda = "SELECT FORMAT(crdate, 'yyyy-MM-dd HH:mm:ss') FROM sysobjects WHERE LOWER(name) = LOWER(?) AND type = 'P'"
                                else:
                                    sql_busqueda = "SELECT CONVERT(varchar(30), crdate, 109) FROM sysobjects WHERE LOWER(name) = LOWER(?) AND type = 'P'"
                                
                                cursor_bd.execute(sql_busqueda, stored_proc)
                                resultado = cursor_bd.fetchone()
                                
                                if resultado and resultado[0]:
                                    # ¡SP encontrado en esta BD!
                                    fecha = resultado[0]
                                    print(f"✅ ENCONTRADO!")
                                    print(f"\n{'='*70}")
                                    print(f"ℹ️  ATENCIÓN: BD en archivo '{db_para_conectar}' es incorrecta")
                                    print(f"✅ SP '{stored_proc}' encontrado en BD real: '{bd_nombre}'")
                                    print(f"    Fecha: {fecha}")
                                    print(f"{'='*70}\n")
                                    # Retornar tupla (fecha, bd_real)
                                    return (fecha, bd_nombre)
                                else:
                                    print(f"No encontrado")
                        except Exception as e_bd:
                            # Error al buscar en esta BD, continuar con la siguiente
                            print(f"Error: {str(e_bd)[:50]}")
                            continue
                    
                    print(f"\n{'='*60}")
                    print(f"❌ SP '{stored_proc}' NO encontrado en ninguna de las {len(todas_bds)} BDs")
                    print(f"{'='*60}\n")
                    return ("No encontrado en DB", None)
                    
                except Exception as e_busqueda:
                    print(f"DEBUG: Error durante búsqueda exhaustiva: {e_busqueda}")
                    import traceback
                    print(f"DEBUG: Traceback: {traceback.format_exc()}")
                    return ("No encontrado en DB", None)
                # --- FIN NUEVO ---

    except Exception as e:
        logging.error(f"Error en obtener_fecha_desde_sp_help: {e}")
        print(f"DEBUG: ❌ Error en obtener_fecha_desde_sp_help: {e}")
        error_str = str(e).lower()
        if 'object does not exist' in error_str or 'does not exist' in error_str:
            return ("No encontrado en DB", None)
        return ("Error de conexión", None)

def _validar_y_corregir_base_datos_para_validacion(base_datos_inicial, ambiente):
    """
    Versión simplificada de validación de BD solo para obtener el case correcto.
    No requiere archivo_path ni log_func, solo valida el nombre de la BD.
    """
    if not base_datos_inicial:
        return ambiente.get('base', 'master')
    
    driver_name = ambiente.get('driver', '')
    if "SQL Server" in driver_name:
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']},{ambiente['puerto']};Database=master;Uid={ambiente['usuario']};Pwd={ambiente['clave']};"
    else:
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']};PORT={ambiente['puerto']};Database=master;Uid={ambiente['usuario']};Pwd={ambiente['clave']};"
    
    try:
        with pyodbc.connect(conn_str, timeout=5, autocommit=True) as conn:
            cursor = conn.cursor()
            
            # Verificar si la BD existe (case-insensitive)
            if "SQL Server" in driver_name:
                cursor.execute("SELECT name FROM sys.databases WHERE LOWER(name) = LOWER(?)", base_datos_inicial)
            else:  # Sybase - especificar owner
                cursor.execute("SELECT name FROM master.dbo.sysdatabases WHERE LOWER(name) = LOWER(?)", base_datos_inicial)
            
            resultado = cursor.fetchone()
            if resultado:
                # La BD existe, retornar el nombre real con el case correcto
                return resultado[0]
            else:
                # La BD no existe, retornar la inicial
                return base_datos_inicial
    except:
        # Si hay error, retornar la inicial
        return base_datos_inicial

def _validar_y_corregir_base_datos(base_datos_inicial, archivo_path, ambiente, log_func=None):
    """
    Valida si la base de datos existe en el ambiente. Si no existe, intenta buscar
    la BD correcta analizando el contenido del archivo.
    
    Args:
        base_datos_inicial: Nombre de la BD extraída del encabezado/USE
        archivo_path: Ruta del archivo .sp/.sql
        ambiente: Dict con datos de conexión
        log_func: Función de logging opcional
    
    Returns:
        str: Nombre de la base de datos validada o corregida
    """
    if not base_datos_inicial:
        return ambiente.get('base', 'master')
    
    # Intentar conectar para validar que la BD existe
    driver_name = ambiente.get('driver', '')
    if "SQL Server" in driver_name:
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']},{ambiente['puerto']};Database=master;Uid={ambiente['usuario']};Pwd={ambiente['clave']};"
    else:
        conn_str = f"Driver={{{driver_name}}};Server={ambiente['ip']};PORT={ambiente['puerto']};Database=master;Uid={ambiente['usuario']};Pwd={ambiente['clave']};"
    
    try:
        with pyodbc.connect(conn_str, timeout=5, autocommit=True) as conn:
            cursor = conn.cursor()
            
            # Verificar si la BD existe (case-insensitive)
            if "SQL Server" in driver_name:
                cursor.execute("SELECT name FROM sys.databases WHERE LOWER(name) = LOWER(?)", base_datos_inicial)
            else:  # Sybase - especificar owner
                cursor.execute("SELECT name FROM master.dbo.sysdatabases WHERE LOWER(name) = LOWER(?)", base_datos_inicial)
            
            resultado = cursor.fetchone()
            if resultado:
                # La BD existe, usar el nombre real (con el case correcto) de la BD
                nombre_real_bd = resultado[0]
                if nombre_real_bd.lower() != base_datos_inicial.lower() and log_func:
                    log_func(f"✅ BD corregida: '{nombre_real_bd}' (case correcto de '{base_datos_inicial}')")
                return nombre_real_bd
            
            # La BD no existe, intentar buscar alternativas
            if log_func:
                log_func(f"⚠️ La BD '{base_datos_inicial}' no existe. Buscando alternativas...")
            
            # Buscar referencias a tablas en el código para inferir la BD
            bases_posibles = set()
            try:
                with open(archivo_path, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read()
                    # Buscar patrones como "database..tabla" o "FROM database.owner.table"
                    patrones = [
                        r'\b([a-z_][a-z0-9_]*)\.\.',  # database..tabla
                        r'FROM\s+([a-z_][a-z0-9_]*)\.',  # FROM database.
                        r'JOIN\s+([a-z_][a-z0-9_]*)\.',  # JOIN database.
                        r'INTO\s+([a-z_][a-z0-9_]*)\.',  # INTO database.
                    ]
                    for patron in patrones:
                        matches = re.finditer(patron, contenido, re.IGNORECASE)
                        for match in matches:
                            db_candidata = match.group(1).lower()
                            # Filtrar nombres comunes que no son BDs
                            if db_candidata not in ['dbo', 'sys', 'information_schema', 'master', 'tempdb', 'model', 'msdb']:
                                bases_posibles.add(db_candidata)
            except:
                pass
            
            # Verificar cuáles de las BDs candidatas existen
            for bd_candidata in bases_posibles:
                if "SQL Server" in driver_name:
                    cursor.execute("SELECT name FROM sys.databases WHERE LOWER(name) = LOWER(?)", bd_candidata)
                else:  # Sybase - especificar owner
                    cursor.execute("SELECT name FROM master.dbo.sysdatabases WHERE LOWER(name) = LOWER(?)", bd_candidata)
                
                resultado = cursor.fetchone()
                if resultado:
                    nombre_real_bd = resultado[0]
                    if log_func:
                        log_func(f"✅ BD corregida: '{nombre_real_bd}' (encontrada en el código del archivo)")
                    return nombre_real_bd
            
            # Si no se encontró ninguna, usar la BD por defecto del ambiente
            if log_func:
                log_func(f"⚠️ No se encontró BD válida. Usando BD del ambiente: '{ambiente.get('base')}'")
            return ambiente.get('base', 'master')
    
    except Exception as e:
        if log_func:
            log_func(f"⚠️ Error validando BD: {str(e)[:200]}. Usando BD inicial.")
        return base_datos_inicial

def catalogar_plan_ejecucion(plan, descripcion, log_func, progress_func=None, resultado_callback=None, carpeta_destino=None):
    """
    Ejecuta el plan de catalogación, procesando cada tarea (archivo-ambiente).
    
    Args:
        resultado_callback: Función que se llama después de catalogar cada archivo
        carpeta_destino: Carpeta específica para guardar los respaldos (opcional)
    """
    resultados = []
    
    # --- RF-CATALOG-RESPALDO-001: Crear carpeta de respaldos con timestamp ---
    if carpeta_destino:
        carpeta_catalogaciones = carpeta_destino
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        carpeta_base = r"C:\ZetaOne\Catalogaciones"
        carpeta_catalogaciones = os.path.join(carpeta_base, f"cataloga{timestamp}")
    
    try:
        os.makedirs(carpeta_catalogaciones, exist_ok=True)
        log_func(f"📁 Carpeta de respaldos: {carpeta_catalogaciones}")
    except Exception as e:
        log_func(f"⚠️ Error creando carpeta de respaldos: {e}")
        logging.error(f"Error creando carpeta de respaldos: {e}")
    
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
        
        # --- RF-CATALOG-RESPALDO-001: Pasar carpeta de respaldos ---
        ok, msg, bd_usada = _catalogar_una_tarea(archivo, ambiente, log_func, carpeta_catalogaciones)
        
        resultado = {
            "ambiente": ambiente['nombre'],
            "archivo": archivo['nombre_archivo'],
            "ruta": archivo.get('rel_path', 'N/A'),
            "fecha_ejecucion": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "estado": "ÉXITO" if ok else "FALLO",
            "detalle": msg,
            "base_datos": bd_usada if bd_usada else 'N/A'
        }
        resultados.append(resultado)
        log_func(f"  -> Resultado: {resultado['estado']} - {resultado['detalle']}")
        
        # Notificar el resultado inmediatamente para actualización progresiva
        if resultado_callback:
            resultado_callback(resultado)

    print(">>> [handler] C. catalogar_plan_ejecucion FINALIZADO.")
    log_func("Proceso de catalogación finalizado.")
    return resultados, carpeta_catalogaciones

def _catalogar_una_tarea(archivo, ambiente, log_func, carpeta_respaldos=None):
    """
    Lógica para catalogar un único archivo en un único ambiente.
    --- RF-CATALOG-RESPALDO-001: Incluye respaldo antes y después ---
    """
    nombre_archivo = archivo['nombre_archivo']
    print(f">>> [handler-task] D. _catalogar_una_tarea INICIADO para '{nombre_archivo}'.")
    
    # Extraer la extensión original del archivo
    extension_original = os.path.splitext(nombre_archivo)[1].lstrip('.')  # Ej: 'sp', 'sql', 'tq'
    
    # 1. Determinar la base de datos y el nombre del SP/SQL
    db_desde_encabezado, sp_desde_encabezado = _extraer_info_desde_encabezado(archivo['path'])
    db_desde_use = _extraer_db_de_sp(archivo['path'])
    base_datos_inicial = archivo.get("db_override") or db_desde_encabezado or db_desde_use or ambiente.get('base')
    
    # Validar y corregir la base de datos si no existe
    base_datos_a_usar = _validar_y_corregir_base_datos(base_datos_inicial, archivo['path'], ambiente, log_func)

    sp_desde_create = _extraer_sp_name_de_sp(archivo['path'])
    nombre_sp_a_usar = archivo.get("sp_name_override") or sp_desde_encabezado or sp_desde_create or os.path.splitext(nombre_archivo)[0]
    nombre_base = os.path.splitext(nombre_archivo)[0]

    print(f">>> [handler-task] E. Parámetros: DB='{base_datos_a_usar}', SP/SQL='{nombre_sp_a_usar}'.")
    
    # ========================================================================
    # NOTA: Ya no verificamos la BD aquí porque la validación ya lo hizo
    # La BD correcta ya viene desde la validación en archivo.get("db_override")
    # ========================================================================
    
    # ========================================================================
    # RF-CATALOG-RESPALDO-001: RESPALDO PREVIO
    # ========================================================================
    path_respaldo_previo = None
    if carpeta_respaldos and nombre_archivo.lower().endswith(('.sp', '.sql')):
        log_func(f"🔍 Extrayendo código previo de '{nombre_sp_a_usar}' desde BD '{base_datos_a_usar}'...")
        print(f">>> [handler-task] DEBUG: Intentando extraer respaldo de SP='{nombre_sp_a_usar}', DB='{base_datos_a_usar}'")
        exito_pre, codigo_pre = extraer_codigo_fuente_db(
            nombre_sp_a_usar, 
            base_datos_a_usar, 
            ambiente, 
            log_func
        )
        
        if exito_pre:
            print(f">>> [handler-task] DEBUG: Código extraído exitosamente. Longitud: {len(codigo_pre)} caracteres")
            metadatos = {'base_datos': base_datos_a_usar}
            exito_archivo, resultado = generar_archivo_respaldo(
                codigo_pre,
                nombre_base,
                'respaldo',
                ambiente,
                carpeta_respaldos,
                metadatos,
                log_func,
                extension_original=extension_original,
                ruta_archivo_original=archivo.get('rel_path', archivo['path'])
            )
            if exito_archivo:
                path_respaldo_previo = resultado
                log_func(f"✅ Respaldo previo creado para SP existente.")
            else:
                log_func(f"⚠️ No se pudo guardar respaldo previo: {resultado}")
        else:
            # No existe el objeto en la BD - esto es normal para SPs nuevos
            print(f">>> [handler-task] DEBUG: SP no existe en BD (es nuevo). Motivo: {codigo_pre}")
            log_func(f"ℹ️ SP '{nombre_sp_a_usar}' no existe en BD - se creará como nuevo.")
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
        # Timeout aumentado para archivos SQL grandes que pueden tener muchos batches
        timeout_conexion = 30 if nombre_archivo.lower().endswith('.sql') else 15
        with pyodbc.connect(conn_str, timeout=timeout_conexion, autocommit=False) as conn:
            # Log connection details (sensitive info masked)
            log_func(f"DEBUG: Conexión establecida para catalogación: {re.sub(r'Pwd=.*?;', 'Pwd=********;', conn_str)}")
            log_func(f"DEBUG: Intentando catalogar archivo: {nombre_archivo} (SP/SQL: {nombre_sp_a_usar}, DB: {base_datos_a_usar})")
            
            cursor = conn.cursor()
            
            # Configurar timeout a nivel de cursor (20 segundos por statement)
            # Esto previene que statements individuales se queden en loop infinito
            try:
                cursor.timeout = 20
                log_func("DEBUG: Timeout de cursor configurado a 20 segundos")
            except:
                log_func("DEBUG: Driver no soporta cursor.timeout, usando solo timeout de conexión")
            
            # --- CORRECCIÓN: Configurar modo de transacción unchained para Sybase ---
            # Algunos SPs como sp_insertar_error requieren modo unchained
            driver_name = ambiente.get('driver', '')
            if "Sybase" in driver_name or "Adaptive Server" in driver_name:
                cursor.execute("SET CHAINED OFF")
                # Agregar timeout a nivel de Sybase (20000 ms = 20 segundos)
                try:
                    cursor.execute("SET LOCK TIMEOUT 20000")
                    log_func("DEBUG: Lock timeout de Sybase configurado a 20 segundos")
                except:
                    log_func("DEBUG: No se pudo configurar LOCK TIMEOUT")
                log_func("DEBUG: Modo de transacción configurado a UNCHAINED para Sybase")
            
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
                        
                        # Protección contra errores de objetos no encontrados
                        try:
                            cursor.execute(batch)
                        except pyodbc.Error as batch_error:
                            error_code = batch_error.args[0] if batch_error.args else ''
                            error_msg = str(batch_error)
                            
                            # Error 208: Object not found - continuar con siguiente batch
                            if ('208' in error_code or 
                                'not found' in error_msg.lower() or
                                'no existe' in error_msg.lower() or
                                'invalid object' in error_msg.lower()):
                                log_func(f"⚠️ Batch {i+1}/{len(batches)} omitido en SP: objeto no encontrado. Error: {error_msg[:200]}")
                                print(f">>> [handler-task] Batch {i+1} OMITIDO en SP por error 208: {error_msg[:150]}")
                                continue  # Continuar con el siguiente batch
                            else:
                                # Otros errores se propagan
                                log_func(f"❌ Error crítico en batch {i+1}/{len(batches)} de SP: {error_msg[:300]}")
                                raise
                
                conn.commit() # Confirmar la transacción para el despliegue del SP
                
                # ================================================================
                # RF-CATALOG-RESPALDO-001: RESPALDO POSTERIOR (SP)
                # ================================================================
                if carpeta_respaldos:
                    # --- CAMBIO: El archivo 'catalogado' debe contener el código ORIGINAL del archivo ---
                    log_func(f"💾 Guardando código catalogado (original del archivo)...")
                    metadatos = {'base_datos': base_datos_a_usar}
                    exito_archivo_post, resultado_post = generar_archivo_respaldo(
                        sp_code,  # Usar el código original del archivo
                        nombre_base,
                        'catalogado',
                        ambiente,
                        carpeta_respaldos,
                        metadatos,
                        log_func,
                        extension_original=extension_original,
                        ruta_archivo_original=archivo.get('rel_path', archivo['path'])
                    )
                    if not exito_archivo_post:
                        log_func(f"⚠️ No se pudo guardar respaldo posterior: {resultado_post}")
                
                return (True, f"Stored Procedure '{nombre_sp_a_usar}' desplegado ({len(batches)} lotes)", base_datos_a_usar)
            
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
                        # Verificar si el batch contiene DROP TABLE y validar existencia
                        batch_upper = batch.strip().upper()
                        if batch_upper.startswith('DROP TABLE'):
                            # Extraer el nombre de la tabla
                            match = re.search(r'DROP\s+TABLE\s+(\[?[\w.]+\]?)', batch, re.IGNORECASE)
                            if match:
                                tabla_nombre_completo = match.group(1)
                                # Limpiar corchetes y extraer solo el nombre de la tabla (después de ..)
                                tabla_nombre = tabla_nombre_completo.replace('[', '').replace(']', '')
                                # Si tiene formato database..tabla, extraer solo la tabla
                                if '..' in tabla_nombre:
                                    tabla_nombre = tabla_nombre.split('..')[-1]
                                elif '.' in tabla_nombre:
                                    # Si tiene formato schema.tabla, tomar solo tabla
                                    tabla_nombre = tabla_nombre.split('.')[-1]
                                
                                # Verificar si la tabla existe con timeout para evitar bloqueos infinitos
                                try:
                                    # Usar parámetros para evitar SQL injection
                                    cursor.execute("SELECT 1 FROM sysobjects WHERE name = ? AND type = 'U'", tabla_nombre)
                                    existe = cursor.fetchone()
                                    if not existe:
                                        log_func(f"ℹ️ Tabla {tabla_nombre} no existe en la BD actual, omitiendo DROP TABLE")
                                        print(f">>> [handler-task] Tabla {tabla_nombre} no existe, omitiendo DROP TABLE")
                                        continue  # Saltar este batch
                                    else:
                                        log_func(f"✓ Tabla {tabla_nombre} existe, ejecutando DROP TABLE")
                                except Exception as e:
                                    log_func(f"⚠️ Error verificando existencia de tabla {tabla_nombre}: {str(e)[:150]}, omitiendo DROP TABLE por seguridad")
                                    print(f">>> [handler-task] Error verificando tabla: {str(e)[:100]}")
                                    continue  # CAMBIO: Omitir en caso de error en lugar de ejecutar de todos modos
                        
                        # La primera ejecución será el "USE [database]"
                        print(f">>> [handler-task] H. Ejecutando batch {i+1}/{len(batches)}...")
                        log_func(f"DEBUG: Ejecutando batch {i+1}/{len(batches)} para {nombre_archivo}:\n{batch.strip()[:200]}...") # Log first 200 chars
                        
                        # Ejecutar batch con manejo de errores para evitar loops infinitos
                        try:
                            # Establecer timeout específico para este statement
                            cursor.execute(batch)
                        except pyodbc.Error as batch_error:
                            error_code = batch_error.args[0] if batch_error.args else ''
                            error_msg = str(batch_error)
                            
                            # Error 208: Object not found - continuar con siguiente batch
                            # Incluir múltiples variantes del mensaje de error
                            if ('208' in error_code or 
                                'not found' in error_msg.lower() or
                                'no existe' in error_msg.lower() or
                                'invalid object' in error_msg.lower()):
                                log_func(f"⚠️ Batch {i+1}/{len(batches)} omitido: objeto no encontrado. Error: {error_msg[:200]}")
                                print(f">>> [handler-task] Batch {i+1} OMITIDO por error 208: {error_msg[:150]}")
                                continue  # Continuar con el siguiente batch sin fallar
                            else:
                                # Otros errores se propagan
                                log_func(f"❌ Error crítico en batch {i+1}/{len(batches)}: {error_msg[:300]}")
                                raise
                
                conn.commit() # Confirmar la transacción para el archivo SQL
                
                # ================================================================
                # RF-CATALOG-RESPALDO-001: RESPALDO POSTERIOR (SQL)
                # ================================================================
                if carpeta_respaldos:
                    # --- CAMBIO: El archivo 'catalogado' debe contener el código ORIGINAL del archivo ---
                    log_func(f"💾 Guardando código catalogado (original del archivo)...")
                    metadatos = {'base_datos': base_datos_a_usar}
                    exito_archivo_post, resultado_post = generar_archivo_respaldo(
                        sql_code,  # Usar el código original del archivo
                        nombre_base,
                        'catalogado',
                        ambiente,
                        carpeta_respaldos,
                        metadatos,
                        log_func,
                        extension_original=extension_original,
                        ruta_archivo_original=archivo.get('rel_path', archivo['path'])
                    )
                    if not exito_archivo_post:
                        log_func(f"⚠️ No se pudo guardar respaldo posterior: {resultado_post}")
                
                return (True, f"Script SQL ejecutado ({len(batches)} lotes)", base_datos_a_usar)
            
            else:
                log_func(f"ADVERTENCIA: Tipo de archivo no soportado para catalogación: {nombre_archivo}")
                return (False, "Tipo de archivo no soportado para catalogación", None)

    except Exception as e:
        # No es necesario un conn.rollback() aquí porque el 'with' se encarga de cerrar
        # la conexión sin hacer commit si ocurre una excepción.
        print(f">>> [handler-task] I. ERROR en _catalogar_una_tarea: {e}\n{traceback.format_exc()}")
        error_detail = f"Error durante la catalogación de '{nombre_archivo}' en '{ambiente['nombre']}': {str(e)}"
        log_func(f"ERROR: {error_detail}\n{traceback.format_exc()}") # Log full traceback to the UI log
        return (False, f"Error: {str(e)}", None)

class VentanaResultadosCatalogacion:
    """Ventana de resultados que se actualiza progresivamente durante la catalogación."""
    
    def __init__(self, parent, carpeta_catalogaciones=None):
        self.win = tk.Toplevel(parent)
        self.win.title("Resultado Catalogación Multiambiente")
        self.win.geometry("1100x600")
        centrar_ventana(self.win, offset_y=20)  # Ligeramente debajo del centro para que no tape otras ventanas
        self.win.transient(parent)
        # No usar grab_set() para permitir interacción con barra de progreso
        
        # Manejar el cierre de la ventana con la X
        self.win.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)
        
        self.carpeta_catalogaciones = carpeta_catalogaciones
        self.resultados = []
        self.mensaje_finalizado_mostrado = False  # Flag para evitar mostrar el mensaje múltiples veces
        
        # Crear TreeView
        columns = ("Ambiente", "Archivo", "Ruta", "Fecha", "Estado", "Detalle")
        ancho_columnas = [120, 200, 250, 140, 80, 250]
        self.tree = ttk.Treeview(self.win, columns=columns, show="headings", height=14)
        for col, ancho_ in zip(columns, ancho_columnas):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho_)
        self.tree.pack(fill="both", expand=True, padx=18, pady=(8, 12), side="top")
        self.tree.tag_configure("ok", background="#bbf7d0")
        self.tree.tag_configure("fallido", background="#fecaca")
        
        # Bind para copiar
        self.tree.bind('<Control-c>', self._copiar_filas)
        self.tree.bind('<Control-C>', self._copiar_filas)
        
        # Frame de botones
        self.btn_frame = tk.Frame(self.win)
        self.btn_frame.pack(fill="x", side="bottom", pady=(1, 7), padx=16)
        
        # Botón para abrir carpeta (se activa cuando hay carpeta)
        if carpeta_catalogaciones and os.path.exists(carpeta_catalogaciones):
            ttk.Button(self.btn_frame, text="📁 Abrir Carpeta de Resultados", 
                      command=self._abrir_carpeta, bootstyle="info-outline").pack(side="left", padx=6)
        
        ttk.Button(self.btn_frame, text="Cerrar", command=self._cerrar_ventana, 
                  bootstyle="secondary").pack(side="right", padx=6)
    
    def mostrar_mensaje_finalizado(self):
        """Muestra el mensaje de catalogación finalizada automáticamente al completar."""
        if self.mensaje_finalizado_mostrado:
            return  # Ya se mostró, no volver a mostrar
        
        self.mensaje_finalizado_mostrado = True
        self._mostrar_dialogo_finalizado()
    
    def _cerrar_ventana(self):
        """Cierra la ventana sin mostrar el mensaje si ya se mostró automáticamente."""
        if self.mensaje_finalizado_mostrado:
            # Ya se mostró el mensaje automáticamente, solo cerrar
            self.win.destroy()
        else:
            # No se ha mostrado, mostrar ahora
            self._mostrar_dialogo_finalizado()
    
    def _mostrar_dialogo_finalizado(self):
        """Muestra el diálogo de catalogación finalizada."""
        # Crear ventana de diálogo personalizada
        dialog = tk.Toplevel(self.win)
        dialog.title("Catalogación Finalizada")
        dialog.geometry("450x150")
        dialog.transient(self.win)
        dialog.grab_set()
        centrar_ventana(dialog)
        
        # Mensaje
        ttk.Label(dialog, text="✅ Catalogación Finalizada", 
                 font=("Segoe UI", 12, "bold")).pack(pady=(20, 10))
        ttk.Label(dialog, text="La catalogación se ha completado exitosamente.",
                 font=("Segoe UI", 10)).pack(pady=5)
        
        # Frame de botones
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        # Botón para abrir carpeta de resultados
        if self.carpeta_catalogaciones and os.path.exists(self.carpeta_catalogaciones):
            ttk.Button(btn_frame, text="📁 Abrir Carpeta de Resultados", 
                      command=lambda: [self._abrir_carpeta(), dialog.destroy(), self.win.destroy()],
                      bootstyle="success").pack(side="left", padx=8)
        
        # Botón Aceptar
        ttk.Button(btn_frame, text="Aceptar", 
                  command=lambda: [dialog.destroy(), self.win.destroy()],
                  bootstyle="primary").pack(side="left", padx=8)
    
    def agregar_resultado(self, resultado):
        """Agrega un resultado a la tabla y lo guarda en la lista."""
        self.resultados.append(resultado)
        tag = "ok" if resultado['estado'] == "ÉXITO" else "fallido"
        self.tree.insert("", "end", values=list(resultado.values()), tags=(tag,))
        # Hacer scroll automático al último elemento
        items = self.tree.get_children()
        if items:
            self.tree.see(items[-1])
        self.win.update_idletasks()
    
    def _copiar_filas(self, event=None):
        items = self.tree.selection()
        if not items:
            return
        registros = []
        for iid in items:
            valores = self.tree.item(iid, "values")
            registros.append('\t'.join(str(val) for val in valores))
        if registros:
            self.win.clipboard_clear()
            self.win.clipboard_append('\n'.join(registros))
    
    def _abrir_carpeta(self):
        try:
            os.startfile(self.carpeta_catalogaciones)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}", parent=self.win)
    
    def destroy(self):
        """Cierra la ventana."""
        self.win.destroy()


def mostrar_resultado_catalogacion(parent, resultados, carpeta_catalogaciones=None):
    """Función legacy para compatibilidad - muestra todos los resultados de una vez."""
    ventana = VentanaResultadosCatalogacion(parent, carpeta_catalogaciones)
    for resultado in resultados:
        ventana.agregar_resultado(resultado)
    # Esperar a que se cierre la ventana
    parent.wait_window(ventana.win)