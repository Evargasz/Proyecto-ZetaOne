import json
from Usuario_basico.migrar_tabla import consultar_tabla_e_indice

# Cargar ambientes
with open('json/ambientes.json', 'r', encoding='utf-8') as f:
    ambs = json.load(f)

# Elegir origen Sybase y destino SQL Server para forzar diferencia
amb_origen = next((a for a in ambs if a['nombre'] == 'SYBREPOR'), None)
amb_destino = next((a for a in ambs if a['nombre'] == 'SQLATM25'), None)

tabla = 'cobis..cl_extend_ente'  # tabla de ejemplo usada en pruebas anteriores

if not amb_origen or not amb_destino:
    print('No se encontraron ambientes requeridos en json/ambientes.json')
    raise SystemExit(1)

print('Ejecutando verificación de estructura: origen=', amb_origen['nombre'], ' destino=', amb_destino['nombre'])
res = consultar_tabla_e_indice(tabla, amb_origen, amb_destino, print, lambda m: print('ERROR:', m), where=None, base_usuario='cobis')
print('\nResultado de consultar_tabla_e_indice:\n')
print(json.dumps(res, ensure_ascii=False, indent=2))
