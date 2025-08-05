import os
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)

def explorar_sd_folder(ruta_base: str, multi_sd: bool = False) -> List[Dict[str, Any]]:
    """
    Escanea una carpeta (o subcarpetas tipo SD) en busca de archivos con extensión .sp, .sql, .tg.
    Devuelve una lista de diccionarios con metadatos relevantes de cada archivo.
    """
    extensiones_validas = ('.sp', '.sql', '.tg')
    archivos_encontrados = []

    logging.debug(f"Ruta base: {ruta_base} -- multi_sd: {multi_sd}")

    if multi_sd:
        try:
            subdirs = sorted(os.listdir(ruta_base))
        except Exception as e:
            logging.error(f"ERROR al listar la carpeta base: {e}")
            return []
        for entradasd in subdirs:
            sd_path = os.path.join(ruta_base, entradasd)
            if os.path.isdir(sd_path) and entradasd.upper().startswith("SD"):
                for carpeta_raiz, _, archivos in os.walk(sd_path):
                    for archivo in archivos:
                        if archivo.lower().endswith(extensiones_validas):
                            path_abs = os.path.join(carpeta_raiz, archivo)
                            rel_path = os.path.relpath(path_abs, ruta_base)
                            partes = rel_path.split(os.sep)
                            archivos_encontrados.append({
                                "path": path_abs,
                                "rel_path": rel_path.replace("\\", "/"),
                                "sd": partes[0] if len(partes) > 0 else None,
                                "carpeta_principal": partes[1] if len(partes) > 1 else None,
                                "modulo": partes[2] if len(partes) > 2 else None,
                                "tipo": os.path.splitext(archivo)[1][1:],
                                "nombre_archivo": os.path.basename(archivo),
                                "fecha_mod": os.path.getmtime(path_abs)
                            })
    else:
        for carpeta_raiz, _, archivos in os.walk(ruta_base):
            for archivo in archivos:
                if archivo.lower().endswith(extensiones_validas):
                    path_abs = os.path.join(carpeta_raiz, archivo)
                    rel_path = os.path.relpath(path_abs, ruta_base)
                    partes = rel_path.split(os.sep)
                    archivos_encontrados.append({
                        "path": path_abs,
                        "rel_path": rel_path.replace("\\", "/"),
                        "sd": partes[0] if len(partes) > 0 else None,
                        "carpeta_principal": partes[1] if len(partes) > 1 else None,
                        "modulo": partes[2] if len(partes) > 2 else None,
                        "tipo": os.path.splitext(archivo)[1][1:],
                        "nombre_archivo": os.path.basename(archivo),
                        "fecha_mod": os.path.getmtime(path_abs)
                    })
    return archivos_encontrados