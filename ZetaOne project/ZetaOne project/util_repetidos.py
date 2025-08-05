from collections import defaultdict
from typing import List, Dict, Any, Tuple

def quitar_repetidos(archivos_candidatos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Dada una lista de archivos candidatos, elimina los que están repetidos por nombre y tipo,
    dejando solo el más reciente cada vez y devolviendo, además, un log de los repetidos encontrados.
    Devuelve (archivos_unicos, repetidos_log)
    """
    files_by_name_ext = defaultdict(list)
    for a in archivos_candidatos:
        key = (a['nombre_archivo'].lower(), a['tipo'].lower())
        files_by_name_ext[key].append(a)
    archivos_unicos = []
    repetidos_log = []
    for key, lst in files_by_name_ext.items():
        if len(lst) == 1:
            archivos_unicos.append(lst[0])
        else:
            mas_nuevo = max(lst, key=lambda x: x['fecha_mod'])
            descartados = [x for x in lst if x != mas_nuevo]
            archivos_unicos.append(mas_nuevo)
            repetidos_log.append({
                "nombre_ext": key,
                "escogido": mas_nuevo,
                "descartados": descartados
            })
    return archivos_unicos, repetidos_log