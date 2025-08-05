import pyodbc
import re
import traceback
from typing import Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger("sybase_utils")
logging.basicConfig(level=logging.INFO)

def _validar_puerto(puerto: str) -> str:
    p = str(puerto).strip()
    if not p.isdigit():
        raise ValueError(f"Puerto inválido (debe ser un número): {puerto}")
    return p

def probar_conexion_amb(amb: Dict[str, Any], log_func=None) -> Tuple[bool, str]:
    """
    Prueba la conexión ODBC a un ambiente Sybase o SQL Server.

    Args:
        amb (dict): Parámetros de conexión.
        log_func (callable, opcional): función para logear mensajes (ej. en el ScrolledText visual).

    Returns:
        Tuple[bool, str]: (Éxito, Mensaje)
    """
    try:
        if log_func: log_func(f"[DEBUG] Ambiente recibido en probar_conexion_amb: {amb}")
        logger.info(f"[DEBUG] Ambiente recibido en probar_conexion_amb: {amb}")
        puerto = _validar_puerto(amb['puerto'])
        if "SQL Server" in amb["driver"]:
            cadena_conexion = (
                f"DRIVER={{{amb['driver']}}};"
                f"SERVER={amb['ip']},{puerto};"
                f"DATABASE={amb['base']};"
                f"UID={amb['usuario']};"
                f"PWD={amb['clave']};"
            )
        else:
            cadena_conexion = (
                f"DRIVER={{{amb['driver']}}};"
                f"SERVER={amb['ip']};"
                f"PORT={puerto};"
                f"DATABASE={amb['base']};"
                f"UID={amb['usuario']};"
                f"PWD={amb['clave']};"
            )
        if log_func: log_func(f"[DEBUG] Cadena de conexión: {cadena_conexion}")
        logger.info(f"[DEBUG] Cadena de conexión: {cadena_conexion}")
        if log_func: log_func("[DEBUG] Intentando conexión...")
        conexion = pyodbc.connect(cadena_conexion, timeout=5)
        conexion.close()
        if log_func: log_func("¡Conexión exitosa!")
        return True, "¡Conexión exitosa!"
    except Exception as e:
        if log_func: log_func(f"Fallo de conexión: {e}")
        logger.error(f"Fallo de conexión: {e}")
        return False, str(e)

def obtener_create_date_sp_help(driver: str, ip: str, port: str, user: str, pwd: str, db: str, sproc: str, log_func=None) -> Optional[Any]:
    """
    Obtiene la fecha de creación de un stored procedure, si es posible.
    """
    try:
        puerto = _validar_puerto(port)

        if "SQL Server" in driver:
            cadena_conexion = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ip},{puerto};"
                f"DATABASE={db};"
                f"UID={user};"
                f"PWD={pwd};"
            )
        else:
            cadena_conexion = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ip};"
                f"PORT={puerto};"
                f"DATABASE={db};"
                f"UID={user};"
                f"PWD={pwd};"
            )
        if log_func: log_func(f"[DEBUG] Cadena de conexión (obtener_create_date_sp_help): {cadena_conexion}")
        logger.info(f"[DEBUG] Cadena de conexión (obtener_create_date_sp_help): {cadena_conexion}")
        conexion = pyodbc.connect(cadena_conexion, timeout=10, autocommit=True)
        cursor = conexion.cursor()
        cursor.execute(f"sp_help '{sproc}'")
        fecha = None
        while True:
            desc = cursor.description
            if desc:
                nombres = [d[0].lower() for d in desc]
                if "create_date" in nombres:
                    idx = nombres.index("create_date")
                    filas = cursor.fetchall()
                    if filas and filas[0][idx]:
                        fecha = filas[0][idx]
                        break
            if not cursor.nextset():
                break
        cursor.close()
        conexion.close()
        return fecha
    except Exception as e:
        if log_func: log_func(f"Error obteniendo create_date: {e}")
        logger.error(f"Error obteniendo create_date: {e}")
        return None

def ejecutar_script_sybase(sql_path: str, amb: Dict[str, Any], log_func=None) -> Tuple[bool, str]:
    """
    Ejecuta un script SQL (Sybase o SQL Server) por lotes.
    """
    script = None
    for encoding in ['utf-8', 'latin1']:
        try:
            with open(sql_path, encoding=encoding) as f:
                script = f.read()
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            if log_func: log_func(f"Error leyendo archivo: {e}\n{traceback.format_exc()}")
            return False, f"Error leyendo archivo: {e}\n{traceback.format_exc()}"
    if script is None:
        if log_func: log_func("No se pudo leer el archivo en utf-8 ni latin1.")
        return False, "No se pudo leer el archivo en utf-8 ni latin1."
    batches = re.split(r'(?im)^[ \t]*go[ \t]*$', script, flags=re.MULTILINE)
    try:
        puerto = _validar_puerto(amb['puerto'])
        if "SQL Server" in amb["driver"]:
            cadena_conexion = (
                f"DRIVER={{{amb['driver']}}};"
                f"SERVER={amb['ip']},{puerto};"
                f"DATABASE={amb['base']};"
                f"UID={amb['usuario']};"
                f"PWD={amb['clave']};"
            )
        else:
            cadena_conexion = (
                f"DRIVER={{{amb['driver']}}};"
                f"SERVER={amb['ip']};"
                f"PORT={puerto};"
                f"DATABASE={amb['base']};"
                f"UID={amb['usuario']};"
                f"PWD={amb['clave']};"
            )
        if log_func: log_func(f"[DEBUG] Cadena de conexión (ejecutar_script_sybase): {cadena_conexion}")
        logger.info(f"[DEBUG] Cadena de conexión (ejecutar_script_sybase): {cadena_conexion}")
        conexion = pyodbc.connect(cadena_conexion, timeout=20)
        cursor = conexion.cursor()
        try:
            cursor.execute("SET CHAINED OFF")
        except Exception as e:
            logger.warning("No se pudo poner en modo unchained:", exc_info=e)
            if log_func: log_func(f"Advertencia: No se pudo poner en modo unchained: {e}")
        for idx, batch in enumerate(batches):
            clean_batch = batch.strip()
            if not clean_batch:
                continue
            try:
                if log_func: log_func(f"== BATCH #{idx+1} ==\n{clean_batch}\n")
                logger.info(f"== BATCH #{idx+1} ==\n{clean_batch}\n")
                cursor.execute(clean_batch)
                conexion.commit()
            except Exception as e:
                cursor.close()
                conexion.close()
                logger.error(f"ERROR EN BATCH #{idx+1}: {e}")
                if log_func: log_func(f"ERROR EN BATCH #{idx+1}: {e}")
                return False, f"Error en batch #{idx + 1}:\n{e}\nBatch SQL:\n{clean_batch}\nTrace:\n{traceback.format_exc()}"
        cursor.close()
        conexion.close()
        if log_func: log_func("Script ejecutado correctamente")
        return True, "OK"
    except Exception as e:
        logger.error(f"Error general ejecutando script SQL: {e}")
        if log_func: log_func(f"Error general ejecutando script SQL: {e}")
        return False, f"{e}\n{traceback.format_exc()}"