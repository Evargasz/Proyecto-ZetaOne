import datetime
from extra_sp_utils import ultra_extraer_sp_bd, limpiar_identificador
from handlers.catalogacion import validar_archivo_sp_local_vs_sybase

def validar_archivos_multiambiente(archivos_unicos, seleccionados_idx, ambientes, progress, label_porc, progreso_win):
    resultados_fila = []
    contador = 0
    for idx in seleccionados_idx:
        arch = archivos_unicos[idx]
        fecha_local = datetime.datetime.fromtimestamp(arch['fecha_mod'])
        if arch['tipo'] == 'sp':
            stored_proc, base_datos = ultra_extraer_sp_bd(arch['path'])
            if isinstance(stored_proc, str):
                stored_proc = limpiar_identificador(stored_proc)
            if isinstance(base_datos, str):
                base_datos = limpiar_identificador(base_datos)
        else:
            stored_proc, base_datos = ("-", "-")
        for amb in ambientes:
            if arch['tipo'] == 'sp' and stored_proc != "No encontrado" and base_datos != "No encontrado":
                fecha_sybase_str, fecha_sybase = validar_archivo_sp_local_vs_sybase(arch, amb, stored_proc, base_datos)
            else:
                fecha_sybase_str = "No existe"
                fecha_sybase = None
            row = (
                str(contador+1),
                amb['nombre'],
                arch['rel_path'],
                fecha_local.strftime('%Y-%m-%d %H:%M'),
                base_datos if base_datos else "-",
                stored_proc if stored_proc else "-",
                fecha_sybase_str
            )
            resultados_fila.append(row)
            contador += 1
            porc = int((contador / (len(seleccionados_idx)*len(ambientes))) * 100)
            progress['value'] = contador
            label_porc.config(text=f"{porc} %")
            progreso_win.update_idletasks()
    return resultados_fila