import os
try:
    import paramiko
    PARAMIKO_DISPONIBLE = True
except ImportError:
    PARAMIKO_DISPONIBLE = False
    paramiko = None
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# ======== CONFIGURACIÓN (usa tus variables directas) ========
ORIGEN_BASE = r"\\192.168.36.17\Compartidos_todos\_Infraestructura\Usuarios\BrayanCordoba\middware"
LINEA_REQUERIDA = "<LineaDeConfiguracion>valor</LineaDeConfiguracion>"
AMBIENTES = {str(i): f"/cobis/ctsusr{i}/" for i in range(1, 19)}
HOST = "192.168.36.28"
USER = "wasadmin"
PASSWORD = "Wasadminc0b1s2022*"

# ============= LÓGICA DE TU BACKEND =============
def modificar_xml(ruta, log_callback=None):
    try:
        with open(ruta, "r+", encoding="utf-8") as f:
            contenido = f.read()
            if LINEA_REQUERIDA not in contenido:
                contenido += "\n" + LINEA_REQUERIDA
                f.seek(0)
                f.write(contenido)
                f.truncate()
                msg = f"[+] Modificado XML: {ruta}"
            else:
                msg = f"[=] XML ya contiene la línea: {ruta}"
            if log_callback: log_callback(msg)
    except Exception as e:
        if log_callback: log_callback(f"[ERROR] {ruta}: {e}")

def asegurar_directorio_remoto(sftp, ruta, log_callback=None):
    try:
        sftp.stat(ruta)
    except FileNotFoundError:
        directorio_padre = os.path.dirname(ruta)
        asegurar_directorio_remoto(sftp, directorio_padre, log_callback)
        sftp.mkdir(ruta)
        if log_callback: log_callback(f"✅ Directorio creado: {ruta}")
    except Exception as e:
        if log_callback: log_callback(f"❌ Error al verificar/crear directorio {ruta}: {e}")

def subir_archivos(origen, destino_xml, destino_jar, log_callback=None):
    if not PARAMIKO_DISPONIBLE:
        if log_callback: log_callback("❌ Error: paramiko no está instalado")
        return False
    transport = paramiko.Transport((HOST, 22))
    transport.connect(username=USER, password=PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)
    asegurar_directorio_remoto(sftp, destino_xml, log_callback)
    asegurar_directorio_remoto(sftp, destino_jar, log_callback)
    for archivo in os.listdir(origen):
        ruta_local = os.path.join(origen, archivo)
        try:
            if archivo.endswith(".xml"):
                modificar_xml(ruta_local, log_callback)
                destino_remoto = destino_xml + archivo
                sftp.put(ruta_local, destino_remoto)
                if log_callback: log_callback(f"[XML] Subido: {archivo} → {destino_remoto}")

            elif archivo.endswith(".jar"):
                destino_remoto = destino_jar + archivo
                sftp.put(ruta_local, destino_remoto)
                if log_callback: log_callback(f"[JAR] Subido: {archivo} → {destino_remoto}")
        except Exception as e:
            if log_callback: log_callback(f"❌ Error al subir {archivo}: {e}")
    sftp.close()
    transport.close()
    if log_callback: log_callback("\n✅ Transferencia completada")

def validar_conexion(host, user, password, log_callback=None):
    if not PARAMIKO_DISPONIBLE:
        if log_callback: log_callback("❌ Error: paramiko no está instalado")
        return False
    try:
        cliente = paramiko.SSHClient()
        cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cliente.connect(host, username=user, password=password)
        cliente.close()
        if log_callback: log_callback("✅ Conexión SSH exitosa")
        return True
    except Exception as e:
        if log_callback: log_callback(f"❌ Error en la conexión SSH: {e}")
        return False

# ========== INTERFAZ GRÁFICA ==========

class CatalogacionCTS(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Catalogacion de CTS")
        self.geometry("440x400")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
      
        # Variables
        self.origen = tk.StringVar()
        self.ambiente = tk.StringVar()
        self.ruta_destino = tk.StringVar()
     
        # -- Título
        tb.Label(self, text="Catalogacion de CTS", bootstyle="dark", font=("-size", 13), anchor="center").pack(pady=(12, 8))
      
        # -- Carpeta Origen
        frm1 = ttk.Frame(self)
        frm1.pack(fill='x', padx=22)
        tb.Label(frm1, text="Seleccione una\ncarpeta origen:", bootstyle="dark", justify='left').pack(side="left", padx=(0,2))
        tb.Entry(frm1, textvariable=self.origen, bootstyle="dark", width=28, state="readonly").pack(side="left", padx=2)
        tb.Button(frm1, text=">", bootstyle="dark", width=3, command=self.abrir_carpeta).pack(side="left")
       
        # -- Combo ambiente
        frm2 = ttk.Frame(self)
        frm2.pack(fill='x', padx=22, pady=(6,0))
        tb.Label(frm2, text="Elije un ambiente:", bootstyle="dark", justify='left').pack(side="left", padx=(0,2))
        combo = tb.Combobox(frm2, textvariable=self.ambiente, bootstyle="dark",values=[f"{k}" for k in AMBIENTES.keys()], state='readonly', width=22)
        combo.pack(side="left", padx=2)
        combo.current(0)
       
        # -- Ruta destino
        frm3 = ttk.Frame(self)
        frm3.pack(fill='x', padx=22, pady=(8,0))
        tb.Label(frm3, text="Escribe la ruta destino:", bootstyle="dark").pack(side="left", padx=(0,2))
        tb.Entry(frm3, textvariable=self.ruta_destino, bootstyle="dark", width=28).pack(side="left", padx=2)
       
        # -- Botones
        frm4 = ttk.Frame(self)
        frm4.pack(pady=(13,6))
        self.btn_catalogar = tb.Button(frm4, text="Catalogar", bootstyle=SUCCESS, width=13, command=self.catalogar)
        self.btn_catalogar.pack(side="left", padx=6)
        tb.Button(frm4, text="Cancelar", bootstyle=DANGER, width=13, command=self.destroy).pack(side="left", padx=6)
        tb.Button(frm4, text="Limpiar", bootstyle=SECONDARY, width=13, command=self.limpiar).pack(side="left", padx=6)
        
        # -- Log
        tb.Label(self, text="Log de operaciones", bootstyle="dark", anchor="w").pack(anchor='w', padx=24, pady=(10,1))
        frm5 = ttk.Frame(self)
        frm5.pack(fill='both', padx=22, expand=True)
        self.txt_log = tk.Text(frm5, height=7, width=38, state='disabled', wrap='word')
        self.txt_log.pack(side="left", fill='both', expand=True)
        scroll = ttk.Scrollbar(frm5, command=self.txt_log.yview)
        scroll.pack(side="right", fill="y")
        self.txt_log['yscrollcommand'] = scroll.set
        # -- Trace para habilitar/deshabilitar botón según validez del directorio
        self.origen.trace_add("write", lambda *a: self._verificar_folder())
        self._verificar_folder()  # el botón empieza deshabilitado

    def _verificar_folder(self):
        origen = self.origen.get()
        if origen and os.path.isdir(origen):
            self.btn_catalogar.config(state='normal')
        else:
            self.btn_catalogar.config(state='disabled')

    def abrir_carpeta(self):
        path = filedialog.askdirectory(initialdir=ORIGEN_BASE)
        if path:
            self.origen.set(path)
        else:
            self.origen.set("")  # si cancela

    def log(self, texto):
        self.txt_log['state'] = 'normal'
        self.txt_log.insert('end', texto+'\n')
        self.txt_log.see('end')
        self.txt_log['state'] = 'disabled'

    def catalogar(self):
        if not PARAMIKO_DISPONIBLE:
            messagebox.showerror("Dependencia Faltante", "Esta funcionalidad requiere 'paramiko'.\n\nInstala con: pip install paramiko")
            return
            
        origen = self.origen.get()
        ambiente = self.ambiente.get()
        ruta_dest = self.ruta_destino.get()
        ruta_valida = r"\\192.168.36.17\Compartidos_todos\_Infraestructura\Usuarios\BrayanCordoba\middware"

        # Exclusivos de la ruta establecida
        if os.path.normcase(os.path.normpath(origen)) != os.path.normcase(os.path.normpath(ruta_valida)):
            messagebox.showerror("Ruta no autorizada", 
                                 "El archivo seleccionando no esta en la ruta permitida, en caso de no aparecer asegurese de estar conectado a la VPN y tener acceso a 'compartidos todos'")
            return
        
        # Valida existencia, aunque el botón ya está protegido
        if not origen:
            messagebox.showwarning("Falta carpeta", "Seleccione una carpeta origen primero.")
            return
        if not os.path.isdir(origen):
            messagebox.showerror("Ruta no encontrada", "La carpeta origen seleccionada no existe o no está disponible.\nNo es posible proceder.")
            self._verificar_folder()
            return
        if not ambiente or ambiente not in AMBIENTES:
            messagebox.showwarning("Falta ambiente", "Seleccione un ambiente válido.")
            return
        if not ruta_dest:
            messagebox.showwarning("Falta ruta", "Ingrese la ruta destino.")
            return
        destino_xml = AMBIENTES[ambiente]
        # Validar conexión SSH
        self.log(f"Validando conexión SSH a {HOST} ...")
        if not validar_conexion(HOST, USER, PASSWORD, self.log):
            self.log("No se pudo establecer conexión. Abortando operación.")
            return
        self.log("Iniciando la transferencia ...")
        subir_archivos(origen, destino_xml, ruta_dest, log_callback=self.log)
        self.log("Catálogo y transferencia finalizados.")

    # DENTRO DE TU CLASE, agrega el método limpiar:
    def limpiar(self):
        self.origen.set("")
        self.ambiente.set(list(AMBIENTES.keys())[0])  # El primer ambiente
        self.ruta_destino.set("")
        self.txt_log['state'] = 'normal'
        self.txt_log.delete('1.0', 'end')
        self.txt_log['state'] = 'disabled'

# mientras se prueba
if __name__ == "__main__":
    app = tb.Window(themename="litera")
    ttk.Button(app, text="Abrir Catalogación CTS", command=lambda: CatalogacionCTS(app)).pack(pady=22)
    app.mainloop()