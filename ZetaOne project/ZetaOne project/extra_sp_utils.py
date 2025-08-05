import re

def ultra_extraer_sp_bd(path):
    """
    Extrae el nombre del stored procedure y la base de datos desde los comentarios de encabezado
    o, si no los encuentra allí, busca en el código SQL.
    """
    try:
        sp_name = None
        bd_name = None
        with open(path, encoding='utf-8') as f:
            # Buscar en los comentarios del encabezado
            for line in f:
                match_sp = re.search(r'Stored procedure:\s*([^\s/]+)', line, re.IGNORECASE)
                match_bd = re.search(r'Base de datos:\s*([^\s/]+)', line, re.IGNORECASE)
                if match_sp:
                    sp_name = match_sp.group(1)
                if match_bd:
                    bd_name = match_bd.group(1)
                if sp_name and bd_name:
                    break
            # Si no encontró, busca en el código SQL real
            if not sp_name or not bd_name:
                f.seek(0)
                content = f.read()
                match_sp_sql = re.search(r'CREATE\s+(?:PROCEDURE|PROC)\s+([a-zA-Z0-9_]+)', content, re.IGNORECASE)
                if match_sp_sql and not sp_name:
                    sp_name = match_sp_sql.group(1)
                match_bd_sql = re.search(r'USE\s+([a-zA-Z0-9_]+)', content, re.IGNORECASE)
                if match_bd_sql and not bd_name:
                    bd_name = match_bd_sql.group(1)
        if not sp_name:
            sp_name = 'No encontrado'
        if not bd_name:
            bd_name = 'No encontrado'
        return (sp_name, bd_name)
    except Exception as e:
        return ('No encontrado', 'No encontrado')

def limpiar_identificador(ident):
    """
    Elimina caracteres no válidos de nombres de stored procedures o bases de datos, 
    comúnmente utilizados al extraer de scripts SQL o comentarios.
    """
    if not ident or not isinstance(ident, str):
        return ""
    # Elimina caracteres especiales frecuentes en nombres recuperados
    ident = ident.replace('\n', '').replace('\r', '').replace('\t', '').strip()
    # Si hay punto, quedarnos solo con la parte real
    if "." in ident:
        ident = ident.split(".")[-1]
    return ident