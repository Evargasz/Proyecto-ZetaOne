import getpass
from tkinter import ttk, messagebox
import tkinter as tk
import os
import json
import re
import datetime
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from styles import etiqueta_titulo, entrada_estandar, boton_accion
from ttkbootstrap.constants import *

class ModificacionesVariasVentana(tk.Toplevel):
    def __init__(self, parent, ambientes_lista, master=None):
        super().__init__(parent)
        self.title("Modificaciones varias")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)

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

        self.btn_continuar = boton_accion(self, texto="Ejecutar modificación", comando=self.on_ejecutar, width=16)
        self.btn_continuar.place(relx=1.0, rely=1.0, x=-230, y=-22, anchor='se')
        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir, width=10)
        self.btn_salir.place(relx=1.0, rely=1.0, x=-40, y=-22, anchor='se')

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.place(x=75, y=y_now+40, width=250, height=15)
        self.progress.lower()

        self.ambientes_lista = ambientes_lista

    def bloquear_campos(self, bloquear=True):
        state = "disabled" if bloquear else "normal"
        self.entry_ambiente.config(state=state)
        self.entry_base.config(state=state)
        self.entry_tabla.config(state=state)
        self.entry_campo.config(state=state)
        self.entry_valor.config(state=state)
        self.entry_condicion.config(state=state)
        self.btn_continuar.config(state=state)
        self.btn_salir.config(state=state)

    def on_ejecutar(self):
        ambiente = self.entry_ambiente.get().strip()
        base = self.entry_base.get().strip()
        tabla = self.entry_tabla.get().strip()
        campo = self.entry_campo.get().strip()
        valor = self.entry_valor.get().strip()
        condicion = self.entry_condicion.get().strip()

        if not all([ambiente, base, tabla, campo, valor, condicion]):
            messagebox.showerror("Error de validación", "Todos los campos son obligatorios.")
            return
        if re.search(r'\bwhere\b', condicion, re.I):
            messagebox.showerror("Error de validación", "No incluya la palabra 'where' en la condición.")
            return
        if re.search(r'\bset\b', valor, re.I):
            messagebox.showerror("Error de validación", "No incluya la palabra 'set' en el nuevo valor.")
            return

        ambiente_obj = next((a for a in self.ambientes_lista if a['nombre'] == ambiente), None)
        if not ambiente_obj:
            messagebox.showerror("Ambiente no encontrado", "Por favor seleccione un ambiente válido.")
            return

        # --- Obtiene y muestra valores previos para CONFIRMAR ---
        self.bloquear_campos(True)
        self.progress.lift()
        self.progress.start(10)
        self.after(200, lambda: self.consulta_y_confirma(ambiente_obj, base, tabla, campo, valor, condicion))

    def consulta_y_confirma(self, ambiente, base, tabla, campo, valor, condicion):
        try:
            import pyodbc
            conn_str = self._cadena_conexion(ambiente, base)
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            select_sql = f"SELECT * FROM {tabla} WHERE {condicion}"
            cursor.execute(select_sql)
            columnas = [column[0] for column in cursor.description]
            filas = cursor.fetchall()
            conn.close()
            if not filas:
                self._finalizar("No se encontraron datos bajo esa condición. No se realiza ninguna modificación.")
                return
            self._respaldar_registros(columnas, filas, tabla, condicion, ambiente['nombre'])
            valores_anteriores = ""
            for fila in filas:
                fila_str = ", ".join([f"{col}={str(val)}" for col, val in zip(columnas, fila)])
                valores_anteriores += f"{fila_str}\n"
            confirm_msg = (
                f"Los siguientes registros serán modificados en:\n"
                f"Ambiente: {ambiente['nombre']} - Base: {base}\n"
                f"Tabla: {tabla}\n"
                f"Campo: {campo}\n"
                f"Nuevo valor: {valor}\n"
                f"Condición: {condicion}\n\n"
                f"VALORES ANTERIORES:\n{valores_anteriores}\n\n"
                "¿Desea continuar la modificación?"
            )
            if not messagebox.askyesno("Confirmar modificación", confirm_msg):
                self._finalizar("Modificación cancelada por el usuario.", finaliza=False, success=False)
                return
            # Si confirmó, sigue con la modificación
            self.after(100, lambda: self.ejecutar_modificacion(ambiente, base, tabla, campo, valor, condicion))
        except Exception as e:
            self._finalizar(f"Error haciendo respaldo previo (SELECT):\n{e}")

    def ejecutar_modificacion(self, ambiente, base, tabla, campo, valor, condicion):
        try:
            import pyodbc
            conn_str = self._cadena_conexion(ambiente, base)
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
        except Exception as e:
            self._finalizar("Error de conexión:\n" + str(e))
            return

        # Obtener tipo de columna mediante fallback (Sybase) o método directo (SQL Server)
        tipo_dato_col = None
        try:
            tipo_dato_col = self._obtener_tipo_columna(cursor, tabla, campo)
            if tipo_dato_col is not None:
                valor = self._validar_tipo(valor, tipo_dato_col)
        except Exception as e:
            messagebox.showwarning("Advertencia", f"No se pudo validar el tipo para {campo}. Se usará el valor como texto.")

        # UPDATE (sin CONVERT para texto, solo para numéricos!)
        update_sql = f"UPDATE {tabla} SET {campo} = ?" + f" WHERE {condicion}"
        try:
            cursor.execute(update_sql, valor)
            filas_afectadas = cursor.rowcount
            conn.commit()
            conn.close()
            self._finalizar(f"¡Modificación exitosa!\nFilas modificadas: {filas_afectadas}", success=True)
        except Exception as e:
            self._finalizar(f"Error al modificar datos:\n{e}")

    def _obtener_tipo_columna(self, cursor, tabla, campo, schema="dbo"):
        # Intenta método ODBC standar, si falla usa fallback Sybase/SQLServer
        try:
            # Método 1: ODBC estándar
            for col in cursor.columns(table=tabla, schema=schema):
                if col.column_name.strip().lower() == campo.strip().lower():
                    return col.type_name.lower()
        except Exception:
            # Método 2: Fallback directo a diccionario de sistema
            try:
                sql = (
                    "SELECT t.name FROM sysobjects o "
                    "JOIN syscolumns c ON c.id = o.id "
                    "JOIN systypes t ON t.type = c.type "
                    "WHERE o.name = ? AND c.name = ?"
                )
                cursor.execute(sql, (tabla, campo))
                row = cursor.fetchone()
                if row:
                    return row[0].lower()
            except Exception as e2:
                print(f"[DEBUG] Fallback type query failed: {e2}")
        return None

    def _finalizar(self, mensaje, finaliza=True, success=False):
        self.progress.stop()
        self.progress.lower()
        self.bloquear_campos(False)
        if success:
            messagebox.showinfo("Resultado", mensaje)
        else:
            messagebox.showerror("Resultado", mensaje)
        if finaliza:
            self.destroy()

    def _cadena_conexion(self, ambiente, base):
        driver = ambiente['driver']
        if driver == 'Sybase ASE ODBC Driver':
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']};"
                f"PORT={ambiente['puerto']};"
                f"DATABASE={base};"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )
        else:
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']},{ambiente['puerto']};"
                f"DATABASE={base};"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )

    def _respaldar_registros(self, columnas, filas, tabla, condicion, ambiente):
        folder = r'C:\ZetaOne\Modificaciones'
        os.makedirs(folder, exist_ok=True)
        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"{tabla}_{ambiente}_{fecha}.txt"
        path = os.path.join(folder, nombre)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"--- Respaldo previo a modificación ---\n")
            f.write(f"Tabla: {tabla}\nAmbiente: {ambiente}\nCondición: {condicion}\nFecha: {fecha}\n\n")
            f.write('\t'.join(columnas) + '\n')
            for fila in filas:
                f.write('\t'.join([str(campo) for campo in fila]) + '\n')

    def _validar_tipo(self, valor, tipo_col):
        if 'int' in tipo_col:
            if not valor.isnumeric():
                raise ValueError("El valor para este campo debe ser un número entero.")
            return int(valor)
        if 'char' in tipo_col or 'text' in tipo_col or 'varchar' in tipo_col or 'univarchar' in tipo_col:
            return str(valor)
        if 'date' in tipo_col or 'time' in tipo_col:
            if not re.match(r"\d{4}-\d{2}-\d{2}", valor):
                raise ValueError("El valor debe ser una fecha con formato AAAA-MM-DD.")
            return valor
        if 'money' in tipo_col or 'decimal' in tipo_col or 'numeric' in tipo_col or 'float' in tipo_col or 'real' in tipo_col:
            try:
                valor_float = float(str(valor).replace(',', '').replace('$', '').strip())
            except Exception:
                raise ValueError("El valor debe ser numérico (ej: 1234.56) para un campo MONEY/DECIMAL/etc. No use comas ni símbolos.")
            return valor_float
        return valor

    def on_salir(self):
        self.destroy()