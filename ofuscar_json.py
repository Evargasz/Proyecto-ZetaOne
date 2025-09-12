import json
import base64

# Nombre del archivo original con las claves
archivo_origen = 'json/ambientes.json'
# Nombre del archivo ofuscado que usará tu aplicación
archivo_destino = 'json/ambientes.dat'

try:
    with open(archivo_origen, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Codificamos el contenido en Base64
    contenido_bytes = contenido.encode('utf-8')
    contenido_codificado = base64.b64encode(contenido_bytes)

    with open(archivo_destino, 'wb') as f:
        f.write(contenido_codificado)

    print(f"¡Éxito! El archivo '{archivo_origen}' ha sido ofuscado y guardado como '{archivo_destino}'.")
    print("Ahora, incluye solo 'ambientes.dat' en tu proyecto y borra 'ambientes.json' de la carpeta 'dist'.")

except Exception as e:
    print(f"Error: No se pudo procesar el archivo. {e}")