import os
from cryptography.fernet import Fernet

# Nombre de la carpeta y el archivo de la clave
carpeta_json = "json"
ruta_clave = os.path.join(carpeta_json, "clave.key")

# Asegurarse de que la carpeta 'json' exista
if not os.path.exists(carpeta_json):
    os.makedirs(carpeta_json)

# Generar y guardar la clave en el archivo
clave = Fernet.generate_key()
with open(ruta_clave, "wb") as archivo_clave:
    archivo_clave.write(clave)

print(f"¡Éxito! El archivo '{ruta_clave}' ha sido creado correctamente.")