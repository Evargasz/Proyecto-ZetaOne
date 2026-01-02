import pyodbc
import time
import sys

# ==============================================================================
# PLANTILLA DE SCRIPT OPTIMIZADO PARA MIGRACIÓN DE GRUPOS
# Reemplaza la lógica de inserción fila por fila por un proceso masivo por lotes.
# ==============================================================================

# --- PASO 1: Adapta estas funciones con tu lógica de conexión real ---

def obtener_conexion_origen():
    """
    Obtiene y retorna una conexión a la base de datos de ORIGEN (ej. Sybase).
    TODO: Reemplazar con la lógica real de tu aplicación.
    """
    try:
        # Ejemplo de cadena de conexión (debes usar la tuya)
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=tu_servidor_origen;'
            r'DATABASE=cob_conta_super;'
            r'UID=tu_usuario;'
            r'PWD=tu_contraseña;'
        )
        # Desactivamos autocommit para un mejor control
        return pyodbc.connect(conn_str, autocommit=False)
    except pyodbc.Error as ex:
        print(f"❌ Error fatal al conectar al ORIGEN: {ex}")
        return None

def obtener_conexion_destino():
    """
    Obtiene y retorna una conexión a la base de datos de DESTINO (ej. SQL Server).
    TODO: Reemplazar con la lógica real de tu aplicación.
    """
    try:
        # Ejemplo de cadena de conexión (debes usar la tuya)
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=tu_servidor_destino;'
            r'DATABASE=tu_db_destino;'
            r'UID=tu_usuario;'
            r'PWD=tu_contraseña;'
        )
        # Desactivamos autocommit para manejar la transacción manualmente
        return pyodbc.connect(conn_str, autocommit=False)
    except pyodbc.Error as ex:
        print(f"❌ Error fatal al conectar al DESTINO: {ex}")
        return None

# --- PASO 2: Función de migración optimizada (no necesita cambios) ---

def migrar_datos_en_lotes(cursor_origen, cursor_destino, select_query: str, insert_sql_template: str):
    """
    Migra datos de un origen a un destino de forma optimizada usando lotes (batches).
    """
    total_insertados = 0
    lote_numero = 1
    batch_size = 1000  # Tamaño del lote, puedes ajustarlo (1000 es un buen punto de partida)

    print("🚀 Iniciando migración optimizada por lotes...")
    log_mensaje = (
        f"   - Leyendo datos del origen con la consulta: {select_query[:200]}...\n"
        f"   - Insertando en destino con la plantilla: {insert_sql_template}\n"
        f"   - Tamaño de lote: {batch_size} registros"
    )
    print(log_mensaje)

    try:
        cursor_destino.fast_executemany = True
        print("✅ 'fast_executemany' activado para un rendimiento superior.")
    except AttributeError:
        print("⚠️ 'fast_executemany' no soportado por el driver. Usando 'executemany' estándar.")

    try:
        cursor_origen.execute(select_query)
        inicio_proceso = time.time()

        while True:
            registros_lote = cursor_origen.fetchmany(batch_size)
            if not registros_lote:
                break

            inicio_lote = time.time()
            cursor_destino.executemany(insert_sql_template, registros_lote)
            fin_lote = time.time()
            
            num_registros_lote = len(registros_lote)
            total_insertados += num_registros_lote
            
            print(f"  Lote {lote_numero} procesado: {num_registros_lote} registros insertados en {fin_lote - inicio_lote:.2f} segundos. Total: {total_insertados}")
            lote_numero += 1

        cursor_destino.connection.commit()
        fin_proceso = time.time()
        print(f"\n✅ Migración por lotes completada con éxito.")
        print(f"   - Total de registros insertados: {total_insertados}")
        print(f"   - Tiempo total del proceso: {fin_proceso - inicio_proceso:.2f} segundos.")

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN (SQLSTATE: {sqlstate}).")
        print(f"   - Mensaje: {ex}")
        print("   - Realizando ROLLBACK de la transacción...")
        cursor_destino.connection.rollback()
        print("   - Rollback completado. No se insertaron datos en este intento.")
        raise
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")
        print("   - Realizando ROLLBACK de la transacción...")
        cursor_destino.connection.rollback()
        print("   - Rollback completado.")
        raise

    return total_insertados

# --- PASO 3: Función principal que orquesta la migración ---

def ejecutar_migracion_de_grupo():
    """
    Función principal que define las consultas y ejecuta el proceso de migración.
    """
    # --- Define aquí tus consultas ---
    # Ejemplo basado en el contexto de tus archivos
    tabla_origen = "cob_conta_super.dbo.sb_balance"
    tabla_destino = "sb_balance_migrada" # Asume que la tabla destino ya existe
    condicion_where = "ba_empresa = 1 AND ba_periodo = 2024"

    # La consulta SELECT completa. Asegúrate que el orden de columnas sea el deseado.
    query_lectura = f"SELECT ba_empresa, ba_cuenta, ba_saldo FROM {tabla_origen} WHERE {condicion_where}"

    # La plantilla INSERT. ¡El número de '?' debe coincidir con el número de columnas en el SELECT!
    plantilla_insercion = f"INSERT INTO {tabla_destino} (empresa, cuenta, saldo) VALUES (?, ?, ?)"

    # --- Ejecución del proceso ---
    conn_origen = None
    conn_destino = None
    try:
        conn_origen = obtener_conexion_origen()
        conn_destino = obtener_conexion_destino()

        if not conn_origen or not conn_destino:
            print("No se pudo establecer una o ambas conexiones. Abortando.")
            return

        cursor_origen = conn_origen.cursor()
        cursor_destino = conn_destino.cursor()

        migrar_datos_en_lotes(cursor_origen, cursor_destino, query_lectura, plantilla_insercion)

    except Exception as e:
        # El error ya se loguea dentro de la función de migración, aquí solo indicamos que el proceso general falló.
        print(f"\nEl proceso de migración de grupo ha fallado. Error: {e}")
        sys.exit(1) # Salir con código de error

    finally:
        # Asegurarse de cerrar siempre las conexiones
        if conn_origen:
            conn_origen.close()
            print("Conexión de origen cerrada.")
        if conn_destino:
            conn_destino.close()
            print("Conexión de destino cerrada.")

if __name__ == '__main__':
    ejecutar_migracion_de_grupo()