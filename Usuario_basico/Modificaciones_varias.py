import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import re
import datetime
import getpass
import threading
import pyodbc
import traceback
from textwrap import dedent
from tkinter import scrolledtext

# --- Imports Corregidos y Optimizados ---
from styles import etiqueta_titulo, entrada_estandar, boton_accion
from util_rutas import recurso_path
from Usuario_basico.historialModificaciones import HistorialModificacionesVen, cargar_historial, guardar_historial
from ttkbootstrap.constants import *

# --- SOLUCIÓN 1: Función de utilidad para centrar ventanas ---
def centrar_ventana(ventana):
    """Centra una ventana Toplevel en la pantalla."""
    ventana.update_idletasks()
    ancho = ventana.winfo_width()
    alto = ventana.winfo_height()
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)
    ventana.geometry(f'{ancho}x{alto}+{x}+{y}')



class ModificacionesVariasVentana(tk.Toplevel):
    def __init__(self, parent, ambientes_lista, master=None):
        super().__init__(parent)
        self.title("Modificaciones varias")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)

        # --- Tu diseño de ventana original, sin cambios ---
        ventana_ancho = 400
        ventana_alto = 380
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)

        y_step = 35
        y_now = 20

        etiqueta_titulo(self, texto="Ambiente:").place(x=20, y=y_now)
        self.entry_ambiente = ttk.Combobox(self, values=[amb['nombre'] for amb in ambientes_lista], state='readonly')
        self.entry_ambiente.place(x=150, y=y_now, width=200)
        y_now += y_step
        
        # --- REQUERIMIENTO 1: Habilitar campos al seleccionar ambiente ---
        self.entry_ambiente.bind("<<ComboboxSelected>>", self._on_ambiente_seleccionado)

        etiqueta_titulo(self, texto="Base de Datos:").place(x=20, y=y_now)
        self.entry_base = entrada_estandar(self)
        self.entry_base.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Tabla:").place(x=20, y=y_now)
        self.entry_tabla = entrada_estandar(self)
        self.entry_tabla.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Campo a modificar:").place(x=20, y=y_now)
        self.entry_campo = entrada_estandar(self)
        self.entry_campo.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Nuevo valor:").place(x=20, y=y_now)
        self.entry_valor = entrada_estandar(self)
        self.entry_valor.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Condición (sin WHERE):").place(x=20, y=y_now)
        self.entry_condicion = entrada_estandar(self)
        self.entry_condicion.place(x=150, y=y_now, width=200)

        # --- REQUERIMIENTO: Reorganización de botones ---
        # --- CORRECCIÓN DEFINITIVA: Usar .place() para el frame y .pack() para los botones internos ---
        btn_frame = tk.Frame(self)
        # Se posiciona el frame de botones debajo de la barra de progreso
        btn_frame.place(x=0, y=y_now + 70, width=ventana_ancho)

        self.btn_continuar = boton_accion(btn_frame, texto="Ejecutar", comando=self.on_ejecutar, width=12)
        self.btn_continuar.pack(side="left", padx=(20, 2)) # Espacio a la izquierda

        self.btn_update_completo = boton_accion(btn_frame, texto="Script SQL", comando=self._on_update_completo, width=12)
        self.btn_update_completo.pack(side="left", padx=2)

        self.btn_historial = boton_accion(btn_frame, texto="Historial", comando=self._mostrar_historial, width=10)
        self.btn_historial.pack(side="left", padx=2)

        self.btn_salir = boton_accion(btn_frame, "Salir", comando=self.on_salir, width=10)
        self.btn_salir.pack(side="left", padx=2)

        # --- CORRECCIÓN: Mover la vinculación y la llamada inicial DESPUÉS de crear los botones ---
        # Vincular la validación a los campos de entrada
        for entry in [self.entry_base, self.entry_tabla, self.entry_campo, self.entry_valor, self.entry_condicion]:
            entry.bind("<KeyRelease>", self._validar_campos_para_ejecutar)

        # Validar el estado inicial (deshabilita el botón de ejecutar)
        self._validar_campos_para_ejecutar()
        
        # --- CORRECCIÓN: Deshabilitar el botón de Script SQL al inicio ---
        self.btn_update_completo.config(state="disabled")

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.place(x=75, y=y_now + 40, width=250, height=15)
        self.progress.lower()

        self.ambientes_lista = ambientes_lista
        
        # --- Carga segura de ambientes relacionados ---
        self.ambientes_rel = {}
        try:
            ruta_relaciones = recurso_path("json", "ambientesrelacionados.json")
            if os.path.exists(ruta_relaciones):
                with open(ruta_relaciones, "r", encoding="utf-8") as f:
                    self.ambientes_rel = json.load(f)
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo cargar 'ambientesrelacionados.json': {e}")

    def bloquear_campos(self, bloquear=True):
        state = "disabled" if bloquear else "normal"
        # Para el combobox, el estado normal es 'readonly'
        self.entry_ambiente.config(state="disabled" if bloquear else "readonly")
        self.entry_base.config(state=state)
        self.entry_tabla.config(state=state)
        self.entry_campo.config(state=state)
        self.entry_valor.config(state=state)
        self.entry_condicion.config(state=state)
        self.btn_continuar.config(state=state)
        self.btn_update_completo.config(state=state)
        self.btn_historial.config(state=state)
        self.btn_salir.config(state=state)

    def on_ejecutar(self):
        """Inicia el proceso de modificación desde los campos de la UI."""
        print("\n--- DEBUG: 1. on_ejecutar() INICIADO ---")
        ambiente = self.entry_ambiente.get().strip()
        base = self.entry_base.get().strip()
        tabla = self.entry_tabla.get().strip()
        campo = self.entry_campo.get().strip()
        valor_bruto = self.entry_valor.get().strip()
        condicion = self.entry_condicion.get().strip()

        if not all([ambiente, base, tabla, campo, valor_bruto, condicion]):
            print("--- DEBUG: ERROR - Campos obligatorios no completados.") # --- CORRECCIÓN: Añadir parent al messagebox ---
            messagebox.showerror("Error de validación", "Todos los campos son obligatorios.", parent=self)
            return
        
        self._iniciar_proceso_modificacion(ambiente, base, tabla, campo, valor_bruto, condicion)

    def _on_update_completo(self):
        """Abre el diálogo para ejecutar un script UPDATE completo."""
        UpdateCompletoDialog(self, self._ejecutar_desde_script, self.entry_ambiente.get())

    def _ejecutar_desde_script(self, parsed_data):
        """Recibe los datos parseados del script y lanza el proceso de modificación."""
        ambiente = self.entry_ambiente.get().strip()
        
        full_table_name = parsed_data['table']
        if '.' in full_table_name:
            parts = full_table_name.split('.', 1)
            base = parts[0]
            tabla = parts[1]
        else:
            messagebox.showerror("Error de Formato", "El nombre de la tabla en el script debe incluir la base de datos (ej: mi_base.dbo.mi_tabla).", parent=self)
            return

        campo = parsed_data['field']
        valor_bruto = parsed_data['value']
        condicion = parsed_data['condition']

        if not ambiente:
            messagebox.showerror("Error de validación", "Debe seleccionar un ambiente en la ventana principal.", parent=self)
            return

        self._iniciar_proceso_modificacion(ambiente, base, tabla, campo, valor_bruto, condicion)

    def _iniciar_proceso_modificacion(self, ambiente, base, tabla, campo, valor_bruto, condicion):
        """Lógica central para validar y lanzar la modificación."""
        # --- REQUERIMIENTO: Iniciar progreso inmediatamente ---
        self.bloquear_campos(True)
        # --- OPTIMIZACIÓN: Hacer la ventana modal para bloquear la ventana padre ---
        # Esto previene que el usuario cierre la aplicación mientras se procesa.
        self.grab_set()

        condicion_lower = condicion.lower()
        # --- CORRECCIÓN 1: Re-añadir la validación de seguridad ---
        # Esta validación previene comandos SQL peligrosos.
        try:
            if any(keyword in condicion_lower for keyword in [';', 'go', 'drop', 'truncate', 'delete from']):
                print("--- DEBUG: ERROR - Condición con palabras clave no permitidas.")
                messagebox.showerror("Error de validación", "La condición contiene palabras clave no permitidas.", parent=self)
                return
        finally:
            self._detener_y_desbloquear_si_error()

        # --- Lógica mejorada para incluir ambientes relacionados ---
        ambientes_a_afectar_nombres = [ambiente]
        if ambiente in self.ambientes_rel:
            ambientes_a_afectar_nombres.extend(self.ambientes_rel[ambiente])
        
        ambientes_dic = {a['nombre']: a for a in self.ambientes_lista}        
        ambientes_obj_a_afectar_con_none = [ambientes_dic.get(nombre) for nombre in ambientes_a_afectar_nombres]
        ambientes_obj_a_afectar = [amb for amb in ambientes_obj_a_afectar_con_none if amb is not None]
        
        # --- CORRECCIÓN 1: Validar que existan ambientes válidos antes de continuar ---
        if not ambientes_obj_a_afectar:
            print("--- DEBUG: ERROR - No se encontraron ambientes válidos para afectar.")
            messagebox.showerror("Error de Configuración", "El ambiente seleccionado (o sus relacionados) no se encuentra en la configuración de ambientes. Verifique el archivo 'ambientesrelacionados.json'.", parent=self)
            self._detener_y_desbloquear_si_error()
            return

        # --- REQUERIMIENTO 2: Validar existencia de BD y Tabla ANTES de confirmar ---
        ambientes_verificados = []
        for amb in ambientes_obj_a_afectar:
            if self._verificar_existencia(amb, base, tabla):
                ambientes_verificados.append(amb)
        
        if not ambientes_verificados:
            messagebox.showerror("No encontrado", f"La base de datos '{base}' y/o la tabla '{tabla}' no se encontraron en ninguno de los ambientes seleccionados o sus relacionados.", parent=self)
            self._detener_y_desbloquear_si_error()
            return

        nombres_ambientes_verificados = [amb['nombre'] for amb in ambientes_verificados]
        # --- FIN REQUERIMIENTO 2 ---

        # --- CORRECCIÓN 1: Obtener tipo de dato y valor limpio ANTES de usarlos ---
        try:
            tipo_dato = self._get_column_type(ambientes_verificados[0], base, tabla, campo)
            valor_limpio = self._adaptar_valor_por_tipo(valor_bruto, tipo_dato)
        except Exception as e:
            print(f"--- DEBUG: ERROR en preparación (get_column_type o adaptar_valor):\n{traceback.format_exc()}")
            messagebox.showerror("Error de Preparación", f"No se pudo verificar el tipo de dato de la columna o adaptar el valor.\n\nError: {e}", parent=self)
            self._detener_y_desbloquear_si_error()
            return

        # Limpiar la condición WHERE
        if re.match(r'^\s*where\s+', condicion, re.IGNORECASE):
            condicion = re.sub(r'^\s*where\s+', '', condicion, count=1, flags=re.IGNORECASE).strip()

        confirm_msg = (
            f"Se intentará ejecutar la modificación en los siguientes ambientes:\n\n"
            f"- {chr(10).join(nombres_ambientes_verificados)}\n\n"
            f"Tabla: {tabla}\n"
            f"Campo: {campo}\n"
            f"Condición: {condicion}\n"
            f"Nuevo Valor (interpretado como {tipo_dato}): {valor_limpio}\n\n"
            "Esta acción puede ser irreversible. ¿Desea continuar?"
        )
        if not messagebox.askyesno("Confirmar Modificación", confirm_msg, parent=self):
            self._detener_y_desbloquear_si_error()
            return

        # --- CORRECCIÓN 1: Iniciar la barra de progreso DESPUÉS de la confirmación ---
        self.progress.lift()
        self.progress.start(10)

        # --- Guardar en historial DESPUÉS de confirmar ---
        try:
            historial = cargar_historial()
            nuevo = {
                "ambiente": ambiente,
                "base": base,
                "tabla": tabla,
                "campo": campo,
                "condicion": condicion
            }
            guardar_historial(historial, nueva_consulta=nuevo)
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo guardar en el historial de modificaciones: {e}")

        # Los campos ya están bloqueados y el progreso iniciado

        # --- Pasar el tipo de dato al hilo para construir la consulta correcta ---
        params = {"base": base, "tabla": tabla, "campo": campo, "valor": valor_limpio, "condicion": condicion, "tipo_dato": tipo_dato}
        print(f"--- DEBUG: 2. Lanzando hilo con parámetros: {params}")
        
        threading.Thread(
            target=self.proceso_de_modificacion,
            args=(ambientes_verificados, params), # Usar la lista verificada
            daemon=True
        ).start()

    def proceso_de_modificacion(self, ambientes_a_modificar, params):
        print("--- DEBUG: 3. Hilo proceso_de_modificacion() INICIADO ---")
        resultados = []
        for amb in ambientes_a_modificar:
            # --- REQUERIMIENTO 3 y 4: Preparar rutas de archivos ---
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_folder = r"C:\ZetaOne\Modificaciones"
            os.makedirs(base_folder, exist_ok=True)
            ruta_backup = os.path.join(base_folder, f"BACKUP_{amb['nombre']}_{params['tabla']}_{timestamp}.txt")
            ruta_resumen = os.path.join(base_folder, f"RESUMEN_{amb['nombre']}_{params['tabla']}_{timestamp}.txt")
            ruta_restore = os.path.join(base_folder, f"RESTAURAR_{amb['nombre']}_{params['tabla']}_{timestamp}.sql")
            try:
                # --- CORRECCIÓN: Conectar a la base por defecto para evitar errores de login ---
                # Se conecta a la base definida en ambientes.json y luego se especifica la base en la consulta.
                conn_str = self._cadena_conexion(amb, amb.get('base', 'master'))
                print(f"--- DEBUG: 4. Procesando ambiente '{amb.get('nombre', 'desconocido')}' ---")
                with pyodbc.connect(conn_str, timeout=5) as conn:
                    with conn.cursor() as cursor:
                        is_sybase = 'sybase' in amb.get('driver', '').lower()
                        
                        # --- CORRECCIÓN: Usar la sintaxis correcta para cada SGBD ---
                        if is_sybase:
                            # Para Sybase, cambiamos de base de datos con USE
                            cursor.execute(f"USE {params['base']}")
                            table_name_for_query = params['tabla']
                        else:
                            # --- CORRECCIÓN: Usar la sintaxis de 3 partes (base.schema.tabla) para SQL Server ---
                            table_name_for_query = f"{params['base']}.dbo.{params['tabla']}"


                        # 1. Respaldo (SELECT)
                        select_sql = f"SELECT * FROM {table_name_for_query} WHERE {params['condicion']}"
                        cursor.execute(select_sql)
                        columnas = [column[0] for column in cursor.description]
                        filas = cursor.fetchall()

                        if not filas:
                            resultados.append(f"[{amb['nombre']}] - INFO: No se encontraron registros que cumplan la condición.")
                            continue
                        
                        # --- REQUERIMIENTO 3, 4 y 5: Generar archivos ---
                        self._respaldar_registros(ruta_backup, columnas, filas, params, amb['nombre'])                        
                        self._generar_resumen_cambios(ruta_resumen, columnas, filas, params, amb['nombre'])
                        self._generar_script_restore(ruta_restore, table_name_for_query, columnas, filas, params, is_sybase)
                        
                        # --- CORRECCIÓN 2: Construir el UPDATE dinámicamente según el tipo de dato y SGBD ---
                        update_sql = f"UPDATE {table_name_for_query} SET {params['campo']} = ? WHERE {params['condicion']}"
                        tipo_dato_lower = params.get('tipo_dato', '').lower()
                        
                        # Para Sybase y tipos numéricos, es obligatorio usar CONVERT
                        if is_sybase and any(t in tipo_dato_lower for t in ['money', 'decimal', 'numeric', 'float', 'real', 'int']):
                            # El tipo de dato en CONVERT debe coincidir con el de la columna
                            sql_type = params.get('tipo_dato').split('(')[0] # Ej: 'decimal(10,2)' -> 'decimal'
                            update_sql = f"UPDATE {table_name_for_query} SET {params['campo']} = CONVERT({sql_type}, ?) WHERE {params['condicion']}"

                        cursor.execute(update_sql, params['valor'])
                        filas_afectadas = cursor.rowcount
                        conn.commit()
                        resultados.append(f"[{amb['nombre']}] - ÉXITO: {filas_afectadas} fila(s) modificada(s).")

            except Exception as e:
                # --- CORRECCIÓN 2: Mejorar el manejo de errores para que no falle si 'amb' es None ---
                nombre_amb_error = amb.get('nombre', 'desconocido') if amb else "desconocido"
                print(f"--- DEBUG: ERROR en el hilo para el ambiente '{nombre_amb_error}':\n{traceback.format_exc()}")
                # --- CORRECCIÓN 3: Convertir la excepción 'e' a string para evitar errores de formato ---
                resultados.append(f"[{nombre_amb_error}] - ERROR: {str(e)}")

        resumen_final = "\n".join(resultados)
        print(f"--- DEBUG: 5. Hilo finalizado. Resumen a mostrar:\n{resumen_final}")
        self.after(0, self._finalizar, resumen_final)

    def _get_column_type(self, amb, base, tabla, campo):
        """Consulta la base de datos para obtener el tipo de dato de una columna."""
        # --- CORRECCIÓN: Usar la base de datos por defecto del ambiente para la consulta de metadatos ---
        # La base de datos ingresada por el usuario (`base`) puede no existir en todos los ambientes relacionados.
        # Para consultar metadatos (sys.columns, sp_columns), es más seguro usar la base por defecto del ambiente.
        conn_str = self._cadena_conexion(amb, amb.get('base', base))
        # La consulta varía ligeramente entre SQL Server y Sybase
        is_sybase = 'sybase' in amb.get('driver', '').lower()
        
        if is_sybase:
            # --- CORRECCIÓN: Usar sp_help, que es más robusto en Sybase (copiado de migrar_tabla.py) ---
            # Este método es más fiable que sp_columns en algunos entornos.
            with pyodbc.connect(conn_str, timeout=8, autocommit=True) as conn:
                cursor = conn.cursor()
                try:
                    # sp_help devuelve varios conjuntos de resultados, necesitamos iterar sobre ellos.
                    # --- CORRECCIÓN: Cambiar al contexto de la base de datos correcta antes de consultar ---
                    cursor.execute(f"USE {base}")
                    cursor.execute(f"sp_help '{tabla}'")
                    while True:
                        # Buscamos el conjunto de resultados que contiene la descripción de las columnas.
                        if cursor.description and 'Column_name' in [d[0] for d in cursor.description] and 'Type' in [d[0] for d in cursor.description]:
                            col_name_idx = [d[0] for d in cursor.description].index('Column_name')
                            type_idx = [d[0] for d in cursor.description].index('Type')
                            
                            for row in cursor.fetchall():
                                if row[col_name_idx] == campo:
                                    return row[type_idx] # Retornamos el tipo y terminamos
                        
                        # Pasamos al siguiente conjunto de resultados. Si no hay más, salimos.
                        if not cursor.nextset():
                            break
                    raise ValueError(f"No se encontró la columna '{campo}' en la tabla '{tabla}' usando sp_help.")
                except Exception as e:
                    raise ValueError(f"Error consultando metadatos de Sybase para '{tabla}.{campo}': {e}")
        else:
            # En SQL Server, es más eficiente consultar las vistas del sistema
            sql = """
                SELECT T.name 
                FROM sys.columns C 
                JOIN sys.types T ON C.user_type_id = T.user_type_id
                WHERE C.object_id = OBJECT_ID(?) AND C.name = ?
            """
            params = [tabla, campo]
            with pyodbc.connect(conn_str, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"No se encontró la columna '{campo}' en la tabla '{tabla}'.")
                
                # Para SQL Server, el resultado está en la primera columna.
                return row[0]

    def _adaptar_valor_por_tipo(self, valor_bruto, tipo_dato):
        """Limpia y convierte el valor de entrada según el tipo de dato de la BD."""
        valor = valor_bruto.strip()
        tipo_dato_lower = tipo_dato.lower()
        

        if any(t in tipo_dato_lower for t in ['money', 'decimal', 'numeric', 'float', 'real', 'int']):
            # Para tipos numéricos, quitar '$' y comas de miles
            return valor.replace('$', '').replace(',', '')
        
        # Para otros tipos (char, varchar, datetime), quitar comillas/paréntesis envolventes
        # --- CORRECCIÓN: Añadir comprobación de longitud para evitar IndexError ---
        if len(valor) > 1 and ((valor.startswith("'") and valor.endswith("'")) or (valor.startswith("(") and valor.endswith(")"))):
            return valor[1:-1]
        return valor

    def _finalizar(self, mensaje):
        print("--- DEBUG: 6. _finalizar() INICIADO para actualizar UI ---")
        self.progress.stop()
        self.progress.lower()
        self.bloquear_campos(False)
        # --- REQUERIMIENTO 1: Limpiar la UI y mantener botones activos ---
        # --- OPTIMIZACIÓN: Liberar la modalidad de la ventana ---
        # Permite que el usuario vuelva a interactuar con la ventana padre.
        self.grab_release()

        self._limpiar_y_bloquear_final()
        
        # Mostrar error si alguna operación falló
        if "ERROR:" in mensaje:
            messagebox.showerror("Resultado con Errores", mensaje, parent=self)
        else:
            messagebox.showinfo("Resultado", mensaje, parent=self)
        
        self.btn_salir.config(state="normal")

    def _on_ambiente_seleccionado(self, event=None):
        """Habilita los campos y botones cuando se selecciona un ambiente."""
        self.bloquear_campos(False)
        # Deshabilitamos el botón de ejecutar hasta que se llenen los campos
        self.btn_continuar.config(state="disabled")
        # Re-habilitamos el botón de script
        self.btn_update_completo.config(state="normal")

    def _validar_campos_para_ejecutar(self, event=None):
        """Verifica si los campos necesarios están llenos para habilitar el botón Ejecutar."""
        # Obtiene el texto de cada campo, quitando espacios en blanco
        campos_llenos = all([
            self.entry_base.get().strip(),
            self.entry_tabla.get().strip(),
            self.entry_campo.get().strip(),
            self.entry_valor.get().strip(),
            self.entry_condicion.get().strip()
        ])
        
        self.btn_continuar.config(state="normal" if campos_llenos else "disabled")

    def _limpiar_y_bloquear_final(self):
        """Limpia los campos y deja solo el de ambiente habilitado."""
        for entry in [self.entry_base, self.entry_tabla, self.entry_campo, self.entry_valor, self.entry_condicion]:
            entry.delete(0, tk.END)
        self.entry_ambiente.set('')
        
        # Bloquea todo excepto el combobox de ambiente
        self.bloquear_campos(True) 
        self.entry_ambiente.config(state="readonly")
        self._validar_campos_para_ejecutar() # Asegura que el botón se deshabilite
        
        # --- CORRECCIÓN: Asegurar que el botón de Script SQL se deshabilite al limpiar ---
        self.btn_update_completo.config(state="disabled")


    def _detener_y_desbloquear_si_error(self):
        """Función auxiliar para detener el progreso y desbloquear la UI si ocurre un error antes del hilo."""
        self.progress.stop()
        self.progress.lower()
        self.grab_release() # Liberar la modalidad si hay un error
        self.bloquear_campos(False)

    def _cadena_conexion(self, ambiente, base):
        """
        Construye una cadena de conexión ODBC robusta.
        Adaptado de la función _build_conn_str que funciona en otros módulos.
        """
        driver = ambiente.get('driver', '') # Obtener driver, sin valor por defecto
        if not driver:
            raise ValueError("El ambiente no tiene un 'driver' ODBC definido.")

        # Configuración de entorno para Sybase, si es necesario
        if 'sybase' in driver.lower():
            odbc_path = os.path.join(os.getcwd(), 'ODBC')
            os.environ['SYBASE'] = odbc_path
            os.environ['SYBASE_OCS'] = 'OCS-15_0'

        if 'sql server' in driver.lower():
            return f"DRIVER={{{driver}}};SERVER={ambiente['ip']},{ambiente['puerto']};DATABASE={base};UID={ambiente['usuario']};PWD={ambiente['clave']};TrustServerCertificate=yes;"
        else:  # Asume Sybase u otro
            return f"DRIVER={{{driver}}};SERVER={ambiente['ip']};PORT={ambiente['puerto']};DATABASE={base};UID={ambiente['usuario']};PWD={ambiente['clave']};"

    def _respaldar_registros(self, ruta_archivo, columnas, filas, params, ambiente_nombre):        
        # --- Ruta de respaldo mejorada y segura ---
        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f"--- Respaldo previo a modificación ---\n")
                f.write(f"Tabla: {params['tabla']}\nAmbiente: {ambiente_nombre}\nCondición: {params['condicion']}\nFecha: {datetime.datetime.now()}\n\n")                
                f.write('\t'.join(columnas) + '\n')
                for fila in filas:
                    f.write('\t'.join([str(campo) for campo in fila]) + '\n')
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo crear el archivo de respaldo: {e}")

    def _generar_resumen_cambios(self, ruta_archivo, columnas, filas, params, ambiente_nombre):
        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f"--- Resumen de Modificación ---\n")
                f.write(f"Ambiente: {ambiente_nombre}\nTabla: {params['tabla']}\nFecha: {datetime.datetime.now()}\n\n")
                f.write(f"Se modificó el campo '{params['campo']}' al valor '{params['valor']}'\n")
                f.write(f"donde la condición era: {params['condicion']}\n\n")
                f.write("--- Registros Afectados (Antes y Después) ---\n")
                
                campo_a_modificar = params['campo']
                idx_campo = columnas.index(campo_a_modificar)

                for fila in filas:
                    valor_antiguo = fila[idx_campo]
                    f.write(f"\nRegistro con PK(s): { {c:v for c,v in zip(columnas, fila) if c != campo_a_modificar} }\n")
                    f.write(f"  - Valor ANTERIOR de '{campo_a_modificar}': {valor_antiguo}\n")
                    f.write(f"  - Valor NUEVO de '{campo_a_modificar}': {params['valor']}\n")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo crear el archivo de resumen: {e}")

    def _generar_script_restore(self, ruta_archivo, nombre_tabla_completo, columnas, filas, params, is_sybase):
        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f"-- Script de Restauración para la modificación en {params['tabla']}\n")
                f.write(f"-- Generado el: {datetime.datetime.now()}\n\n")
                
                if is_sybase:
                    f.write(f"USE {params['base']}\nGO\n\n")

                for fila in filas:
                    update_statement = f"UPDATE {nombre_tabla_completo} SET "
                    set_clauses = []
                    where_clauses = []
                    
                    for col, val in zip(columnas, fila):
                        # Para la cláusula WHERE, siempre usamos los valores originales
                        where_clauses.append(f"[{col}] = '{str(val).replace("'", "''")}'")                        
                        # Para la cláusula SET, restauramos el valor original del campo modificado
                        if col == params['campo']:
                            set_clauses.append(f"[{col}] = '{str(val).replace("'", "''")}'")                            

                    update_statement += ", ".join(set_clauses)
                    update_statement += " WHERE " + " AND ".join(where_clauses) + ";\n"
                    f.write(update_statement)
                
                if is_sybase:
                    f.write("\nGO\n")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo crear el script de restauración: {e}")

    def _verificar_existencia(self, amb, base, tabla):
        """Verifica si la base y la tabla existen en un ambiente dado."""
        try:
            conn_str = self._cadena_conexion(amb, amb.get('base', 'master'))
            with pyodbc.connect(conn_str, timeout=3) as conn:
                cursor = conn.cursor()
                                
                is_sybase = 'sybase' in amb.get('driver', '').lower()

                if is_sybase:
                    # Para Sybase, la forma más fiable es intentar usar los objetos.
                    # Si falla, la excepción lo captura y devuelve False.
                    cursor.execute(f"USE {base}")
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE 1=0")                    
                    return True # Si ambas líneas se ejecutan, los objetos existen.
                else: # SQL Server
                    cursor.execute("SELECT COUNT(*) FROM sys.databases WHERE name = ?", base)
                    if cursor.fetchone()[0] == 0: return False
                    cursor.execute(f"SELECT COUNT(*) FROM {base}.sys.tables WHERE name = ?", tabla)
                    return cursor.fetchone()[0] > 0
        except Exception:
            # Cualquier excepción (ej. BD no existe, tabla no existe, timeout) significa que no es accesible.
            return False

    def on_salir(self):
        self.destroy()

    def _mostrar_historial(self):
        def rellenar_campos(ambiente, base, tabla, campo, condicion):
            self.entry_ambiente.set(ambiente)
            self.entry_base.delete(0, tk.END)
            self.entry_base.insert(0, base)
            self.entry_tabla.delete(0, tk.END)
            self.entry_tabla.insert(0, tabla)
            self.entry_campo.delete(0, tk.END)
            self.entry_campo.insert(0, campo)
            self.entry_condicion.delete(0, tk.END)
            self.entry_condicion.insert(0, condicion)
            # --- CORRECCIÓN: Validar campos después de rellenar desde el historial ---
            self._validar_campos_para_ejecutar()

        HistorialModificacionesVen(self, callback_usar=rellenar_campos)

# --- REQUERIMIENTO: Nueva clase para el diálogo de Script SQL ---
class UpdateCompletoDialog(tk.Toplevel):
    def __init__(self, parent, callback_ejecutar, ambiente_seleccionado):
        super().__init__(parent)
        self.callback_ejecutar = callback_ejecutar
        self.title("Ejecutar Script de Modificación")
        self.geometry("600x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # --- SOLUCIÓN 1: Centrar la ventana al abrirse ---
        centrar_ventana(self)

        # --- REQUERIMIENTO 2: Mostrar ambiente(s) a afectar ---
        ambientes_rel = parent.ambientes_rel.get(ambiente_seleccionado, [])
        afectados_str = ambiente_seleccionado
        if ambientes_rel:
            afectados_str += f" (y relacionados: {', '.join(ambientes_rel)})" # type: ignore
        
        info_frame = tk.Frame(self)
        info_frame.pack(fill="x", padx=10, pady=(10, 5))
        etiqueta_titulo(info_frame, texto=f"Ambiente(s) a afectar: {afectados_str}", wraplength=580).pack(anchor='w')
        
        info_text = "Pegue un script UPDATE (una tabla, un campo):\nUPDATE base.dbo.tabla SET campo = 'valor' WHERE condicion"
        etiqueta_titulo(info_frame, texto=info_text, justify="left").pack(pady=(5,0), anchor='w')

        self.sql_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=8, font=("Courier New", 10))
        self.sql_text.pack(pady=5, padx=10, fill="both", expand=True)
        self.sql_text.focus_set()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        self.btn_ejecutar = boton_accion(btn_frame, "Ejecutar Script", self.on_ejecutar_script)
        self.btn_ejecutar.pack(side="left", padx=10)
        self.btn_cancelar = boton_accion(btn_frame, "Cancelar", self.destroy)
        self.btn_cancelar.pack(side="left", padx=10)

        # --- REQUERIMIENTO 2: Barra de progreso ---
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=(0, 5))
        self.progress.lower() # Ocultarla al inicio

    def on_ejecutar_script(self):
        sql = self.sql_text.get("1.0", tk.END).strip()
        if not sql:
            messagebox.showwarning("Entrada vacía", "Por favor, ingrese un script SQL.", parent=self)
            return

        # --- MEJORA: Usar una expresión regular para una validación más robusta ---
        if not sql.lower().startswith("update") or not re.search(r'\bwhere\b', sql, re.IGNORECASE):
            messagebox.showerror("Error de Formato", "El script debe ser una sentencia UPDATE y debe contener una cláusula WHERE.", parent=self)
            return

        regex = re.compile(
            r"^\s*UPDATE\s+(?P<table>[\w\.]+)\s+SET\s+(?P<field>\w+)\s*=\s*(?P<value>.+?)\s+WHERE\s+(?P<condition>.+?)\s*;?\s*$",
            re.IGNORECASE | re.DOTALL
        )
        match = regex.match(sql)

        if not match:
            messagebox.showerror("Error de Formato", "No se pudo procesar el script. Asegúrese de que sigue el formato:\nUPDATE base.dbo.tabla SET campo = valor WHERE condicion", parent=self)
            return

        # --- SOLUCIÓN 2: Deshabilitar controles en lugar de cerrar la ventana ---
        self.sql_text.config(state="disabled")
        self.btn_ejecutar.config(state="disabled")
        self.btn_cancelar.config(text="Cerrar") # Cambiar texto para más claridad
        
        # Iniciar la barra de progreso
        self.progress.lift() # type: ignore
        self.progress.start(10) # type: ignore

        self.callback_ejecutar(match.groupdict())
        # La ventana ya no se destruye aquí. El usuario lo hará con el botón "Cerrar".