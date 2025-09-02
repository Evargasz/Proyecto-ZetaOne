import pyodbc

# Simulando el ambiente importado desde ambientes.py
ambiente = {
    "nombre": "Cobis26",
    "ip": "192.168.36.62",
    "puerto": "7026",
    "usuario": "sa_cobis",
    "clave": "4dm1Nc0b1S",
    "base": "cobis",
    "driver": "Sybase ASE ODBC Driver"
}

# Armando la cadena de conexión
conn_str = (
    f"DRIVER={{{ambiente['driver']}}};"
    f"SERVER={ambiente['ip']};"
    f"PORT={ambiente['puerto']};"
    f"DATABASE={ambiente['base']};"
    f"UID={ambiente['usuario']};"
    f"PWD={ambiente['clave']};"
)

try:
    print(f"Probando conexión a Sybase ambiente: {ambiente['nombre']}")
    conn = pyodbc.connect(conn_str, timeout=5)
    print("¡Conexión exitosa a Sybase!")
except Exception as e:
    print("Error al conectar a Sybase:", e)
finally:
    try:
        conn.close()
    except:
        pass

import platform
print(platform.architecture())