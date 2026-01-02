import pyodbc
import json
import os

# Cargar ambientes desde el archivo JSON
def cargar_ambiente(nombre_ambiente):
    """Carga la configuración de un ambiente desde ambientes.json"""
    json_path = os.path.join("json", "ambientes.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            ambientes = json.load(f)
        for amb in ambientes:
            if amb["nombre"].upper() == nombre_ambiente.upper():
                return amb
        return None
    except Exception as e:
        print(f"Error cargando ambientes: {e}")
        return None

def construir_cadena_conexion(ambiente):
    """Construye la cadena de conexión ODBC desde un diccionario de ambiente"""
    if not ambiente:
        return None
    
    driver = ambiente.get("driver", "Sybase ASE ODBC Driver")
    ip = ambiente.get("ip")
    puerto = ambiente.get("puerto")
    usuario = ambiente.get("usuario")
    clave = ambiente.get("clave")
    base = ambiente.get("base", "cobis")
    
    if "Sybase" in driver:
        # Formato para Sybase: SERVER=ip; PORT=puerto (separados)
        return f"DRIVER={{{driver}}};SERVER={ip};PORT={puerto};DATABASE={base};UID={usuario};PWD={clave};"
    else:
        # Formato para SQL Server: Server=ip,puerto
        return f"DRIVER={{{driver}}};Server={ip},{puerto};Database={base};Uid={usuario};Pwd={clave};"

# --- CONFIGURACIÓN ---
AMBIENTE = "SYBCOB25"  # Cambia esto si deseas usar otro ambiente
QUERY = '''
SELECT ba_empresa, ba_cuenta, ba_periodo, ba_corte, ba_oficina, ba_saldo, ba_saldo_me, ba_saldo_mn
FROM cob_conta_super..sb_balance
WHERE ba_empresa = 1 AND ba_periodo = 2024 AND ba_corte = 182
'''

def main():
    # Cargar configuración del ambiente
    ambiente = cargar_ambiente(AMBIENTE)
    if not ambiente:
        print(f"Error: No se encontró el ambiente '{AMBIENTE}'")
        return
    
    # Construir cadena de conexión
    conn_str = construir_cadena_conexion(ambiente)
    if not conn_str:
        print("Error: No se pudo construir la cadena de conexión")
        return
    
    print(f"Conectando a: {AMBIENTE}")
    print(f"Server: {ambiente['ip']}:{ambiente['puerto']}")
    print(f"Database: {ambiente['base']}")
    print("-" * 60)
    
    try:
        conn = pyodbc.connect(conn_str, timeout=8)
        cursor = conn.cursor()
        print("Ejecutando consulta...")
        cursor.execute(QUERY)
        rows = cursor.fetchall()
        
        print(f"\n✓ Total de registros leídos: {len(rows)}")
        
        if rows:
            print("\nPrimeros 5 registros:")
            print(f"{'Empresa':<10} {'Cuenta':<15} {'Periodo':<10} {'Corte':<10} {'Oficina':<10} {'Saldo':<15} {'Saldo ME':<15} {'Saldo MN':<15}")
            print("-" * 100)
            for i, row in enumerate(rows[:5]):
                print(f"{row[0]:<10} {row[1]:<15} {row[2]:<10} {row[3]:<10} {row[4]:<10} {str(row[5]):<15} {str(row[6]):<15} {str(row[7]):<15}")
            
            if len(rows) > 5:
                print(f"\n... y {len(rows) - 5} registros más")
        else:
            print("No se encontraron registros con la condición dada.")
            
        cursor.close()
        conn.close()
        
    except pyodbc.Error as e:
        print(f"❌ Error ODBC: {e}")
        print(f"Estado ODBC: {e.args[0]}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
