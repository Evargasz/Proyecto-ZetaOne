import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
from datetime import datetime, timedelta
from styles import etiqueta_titulo, entrada_estandar, boton_accion
import ttkbootstrap as tb

class ActualizaFechaContabilidadVentana(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Actualizar Fecha de Contabilidad")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        ventana_ancho = 420
        ventana_alto = 270
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)

        # Carga ambientes
        self.proyecto_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.json_path = os.path.join(self.proyecto_base, "json", "ambientes.json")
        self.ambientes = []
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.ambientes = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar ambientes.json:\n{e}")
            self.destroy()
            return

        self._armar_interfaz()

    def _armar_interfaz(self):
        y_row = 20

        etiqueta_titulo(self, texto="Ambiente:").place(x=26, y=y_row)
        nombres_ambiente = [a['nombre'] for a in self.ambientes]
        self.combo_ambiente = ttk.Combobox(self, values=nombres_ambiente, state="readonly", width=26)
        self.combo_ambiente.place(x=125, y=y_row)

        # Periodo (Año)
        y_row += 40
        etiqueta_titulo(self, texto="Periodo (Año):").place(x=26, y=y_row)
        years = [str(y) for y in range(2000, 2041)]
        self.combo_periodo = ttk.Combobox(self, values=years, state="readonly", width=12)
        self.combo_periodo.place(x=168, y=y_row)

        # Corte
        y_row += 40
        etiqueta_titulo(self, texto="Corte (Día):").place(x=26, y=y_row)
        self.cortes_display, self.cortes_dict = self.generar_cortes()
        self.combo_corte = ttk.Combobox(self, values=self.cortes_display, state='readonly', width=28)
        self.combo_corte.place(x=120, y=y_row)

        # Nuevo estado
        y_row += 40
        etiqueta_titulo(self, texto="Nuevo Estado:").place(x=26, y=y_row)
        self.combo_estado = ttk.Combobox(self, values=["A", "C", "V"], state="readonly", width=10)
        self.combo_estado.place(x=140, y=y_row)

        # Progress
        self.progress = ttk.Progressbar(self, orient='horizontal', length=320, mode='indeterminate')
        self.progress.place(x=40, y=200)

        # Botones
        self.btn_actualizar = boton_accion(self, "Actualizar", comando=self.on_actualizar, width=14)
        self.btn_actualizar.place(x=170, y=230)
        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir, width=10)
        self.btn_salir.place(x=300, y=230)

    def generar_cortes(self):
        cortes_display = []
        cortes_dict = {}
        fecha = datetime(2000, 1, 1)  # Año base
        for i in range(366):
            consecutivo = i + 1
            texto = f'{fecha.strftime("%d de %B")} - {consecutivo}'
            cortes_display.append(texto)
            cortes_dict[texto] = consecutivo
            fecha += timedelta(days=1)
            if fecha.month == 2 and fecha.day == 29:
                continue
            if fecha.month == 3 and fecha.day == 1 and not fecha.year % 4 == 0:
                fecha = fecha.replace(month=3, day=1)
        return cortes_display, cortes_dict

    def on_salir(self):
        self.destroy()

    def on_actualizar(self):
        # Recopila los valores de entrada
        ambiente_nombre = self.combo_ambiente.get().strip()
        periodo = self.combo_periodo.get().strip()
        corte_str = self.combo_corte.get()
        estado = self.combo_estado.get().strip()

        # Validaciones básicas  
        if not ambiente_nombre or not periodo or not corte_str or not estado:
            messagebox.showwarning("Campos vacíos", "Por favor complete todos los campos.")
            return
        try:
            periodo = int(periodo)
            corte = int(self.cortes_dict.get(corte_str))
        except Exception as e:
            messagebox.showerror("Error formato", f"Periodo o corte inválidos.\n{e}")
            return

        ambiente = next((a for a in self.ambientes if a['nombre'] == ambiente_nombre), None)
        if not ambiente:
            messagebox.showerror("Ambiente no encontrado", "Por favor seleccione un ambiente válido.")
            return

        # ------ 1. Confirmación previa de cambio ------
        # Obtiene el estado actual antes
        driver = ambiente['driver']
        if driver == 'Sybase ASE ODBC Driver':
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']};"
                f"PORT={ambiente['puerto']};"
                f"DATABASE=cob_conta;"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']},{ambiente['puerto']};"
                f"DATABASE=cob_conta;"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )

        def consulta_estado_actual():
            try:
                import pyodbc
                conn = pyodbc.connect(conn_str, timeout=5)
                cursor = conn.cursor()
                cursor.execute("SELECT co_estado FROM cb_corte WHERE co_periodo = ? AND co_corte = ? AND co_empresa = 1", (periodo, corte))
                row = cursor.fetchone()
                conn.close()
                return row[0] if row else None
            except Exception as ex:
                return None

        estado_actual = consulta_estado_actual()
        if estado_actual is None:
            if not self.ask_proceed_on_missing():
                return

        else:
            msg = (
                f"Estado actual para Periodo: {periodo}, Corte: {corte} es: '{estado_actual}'.\n"
                f"¿Desea modificarlo a '{estado}' en ambiente '{ambiente['nombre']}'?"
            )
            if not messagebox.askyesno("Confirmar actualización", msg):
                return

        # BLOQUEA UI y lanza threading para actualización
        self.progress.start()
        self._deshabilitar_ui(True)
        threading.Thread(
            target=self._proceso_actualizacion, args=(ambiente, periodo, corte, estado, conn_str),
            daemon=True
        ).start()

    def ask_proceed_on_missing(self):
        msg = (
            "No se encontró el registro para el periodo y corte seleccionados.\n\n"
            "¿Desea continuar e intentar actualizar de todos modos?"
        )
        return messagebox.askyesno("Confirmar actualización", msg)

    def _proceso_actualizacion(self, ambiente, periodo, corte, estado, conn_str):
        import pyodbc
        exito, mensaje_resultado = False, ""
        try:
            conn = pyodbc.connect(conn_str, timeout=8, autocommit=True)
            cursor = conn.cursor()
            update_sql = (
                "UPDATE cb_corte SET co_estado = ? WHERE co_periodo = ? AND co_corte = ? AND co_empresa = 1"
            )
            result = cursor.execute(update_sql, (estado, periodo, corte))
            filas_afectadas = result.rowcount if hasattr(result, 'rowcount') else None
            conn.close()
            if filas_afectadas and filas_afectadas > 0:
                exito = True
                mensaje_resultado = (f"Actualización exitosa:\n"
                                     f"Periodo: {periodo}\nCorte: {corte}\n"
                                     f"Nuevo estado: '{estado}'\n"
                                     f"Ambiente: {ambiente['nombre']}.")
            else:
                mensaje_resultado = (f"No se encontró ningún registro que actualizar.\n"
                                     f"Verifique los datos e intente nuevamente.")
        except Exception as e:
            if "ODBC" in str(e) or "connect" in str(e) or "timeout" in str(e):
                mensaje_resultado = "No fue posible establecer conexión. Revise la conexión al ambiente."
            else:
                mensaje_resultado = f"Ocurrió un error inesperado: {e}"
        finally:
            # Actualiza UI con resultado
            self.after(0, self.progress.stop)
            self.after(0, self._habilitar_ui)
            if exito:
                self.after(0, lambda: messagebox.showinfo("Éxito", mensaje_resultado))
            else:
                self.after(0, lambda: messagebox.showerror("Resultado", mensaje_resultado))

    def _deshabilitar_ui(self, state):
        widget_state = 'disabled' if state else 'normal'
        for w in (self.combo_ambiente, self.combo_periodo, self.combo_corte, self.combo_estado, self.btn_actualizar, self.btn_salir):
            w.configure(state=widget_state)

    def _habilitar_ui(self):
        self._deshabilitar_ui(False)