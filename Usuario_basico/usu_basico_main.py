import tkinter as tk
from tkinter import messagebox, Toplevel, Entry, Label, Button, Frame
from PIL import Image, ImageTk
import os 

class usuBasicoMain(Frame):
    def __init__(self, master, controlador):
        super().__init__(master)
        self.root = master
    
    #btn usar
        self.master = master
    
    # Configuración de ventana
        self.root.title("ZetaOne")
        ventana_ancho = 790
        ventana_alto = 600
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.root.resizable(False, False)

    #funcionalidades 
        self.funcionalidades = [
            {"titulo":"desbloquear usuario", "desc":"...", "accion":self.usar_desbloquear_usuario},
            {"titulo":"autorizar tablas", "desc": "...", "accion":self.usar_autorizar_tablas},
            {"titulo": "actualizar fechas de contabilidad", "desc": "...", "accion":self.usar_actualizar_fecha_cont}
        ]
    
    #variables de la barra de busqueda
        self.texto_busqueda = ""
        self.placeholder_text = "¿Qué deseas hacer?"
    
    #icono
        self.root.iconbitmap("imagenes_iconos/Zeta99.ico")

        #otras variables
    #lista de ambientes
        self.lista_de_ambientes = []
    
        
        # Variables de control del filtro
        self.filtro_acceso_rapido = False
        self.color_boton_activo = "#FF3131"
        self.color_boton_default = "#F2F2F2"

        # 1. SIDEBAR IZQUIERDA
        self.sidebar = tk.Frame(self.root, bg="#fff", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.armar_sidebar()

        # 2. ÁREA PRINCIPAL DERECHA
        self.main_frame = tk.Frame(self.root, bg="#F7F7F7")
        self.main_frame.pack(side="right", fill="both", expand=True)
        self.armar_area_principal()

    def armar_sidebar(self):
        usuario_img = Image.open("imagenes_iconos/userico.png")  # Llama imagen de usuario
        usuario_img = usuario_img.resize((120, 120))
        self.usuario_icon = ImageTk.PhotoImage(usuario_img)
        tk.Label(self.sidebar, image=self.usuario_icon, bg="#fff").pack(pady=(30, 10))

        # Texto de bienvenida
        bienvenida_lbl = tk.Label(self.sidebar, text="BIENVENIDO\n*usuario del cp*", bg="#fff", font=("Arial", 12))
        bienvenida_lbl.pack(pady=(0, 300))

        # Botón Salir
        btn_salir = tk.Button(self.sidebar, text="salir", bg="#333", fg="#fff", font=("Arial", 12), height=1,
                              relief="flat", width=10, command=self.salir)
        btn_salir.pack(side="bottom", pady=20)

    def armar_area_principal(self):
        # ------- Barra superior: búsqueda -------
        barra_superior = tk.Frame(self.main_frame, bg="#fff")
        barra_superior.pack(fill="x", padx=40, pady=20)

        # Campo de búsqueda expandido hasta la lupa
        self.entry_busqueda = tk.Entry(barra_superior, font=("Arial", 14))
        self.entry_busqueda.insert(0, self.placeholder_text)
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 0), ipady=4)

        def clear_placeholder_busqueda(event):
            if self.entry_busqueda.get() == self.placeholder_text:
                self.entry_busqueda.delete(0, tk.END)
                self.entry_busqueda.config(foreground='black', show="")

        def add_placeholder_busqueda(event):
            if self.entry_busqueda.get() == "":
                self.entry_busqueda.insert(0, self.placeholder_text)
                self.entry_busqueda.config(foreground='black', show="")

        self.entry_busqueda.bind("<FocusIn>", clear_placeholder_busqueda)
        self.entry_busqueda.bind("<FocusOut>", add_placeholder_busqueda)
        self.entry_busqueda.bind("<Return>", lambda event: self.accion_busqueda())

        # Botón de búsqueda (lupa)
        lupa_img = Image.open("imagenes_iconos/lupa.png")
        lupa_img = lupa_img.resize((22, 22))
        self.lupa_icon = ImageTk.PhotoImage(lupa_img)

        btn_lupa = tk.Button(barra_superior, image=self.lupa_icon, relief="flat",
                             bg="#fff", cursor="hand2", bd=0,
                             command=self.accion_busqueda)
        btn_lupa.pack(side="left")

        # -------- Filtros abajo de la barra --------
        filtros_frame = tk.Frame(self.main_frame,
                                bg="#fff")
        filtros_frame.pack(anchor="w",
                           padx=56,
                           pady=(5, 10))

        self.filtro_todos = tk.Button(filtros_frame,
                                      text="Todos",
                                      bg="#ddd",
                                      relief="groove",
                                      command=self.mostrar_todos)
        self.filtro_todos.pack(side="left",
                               padx=(0, 10))

        self.boton_acceso_rapido = tk.Button(
            filtros_frame, text="Acceso rápido",
            bg=self.color_boton_default,
            font=("Arial", 10),
            command=self.toggle_acceso_rapido,
            width=12
        )
        self.boton_acceso_rapido.pack(side="left",
                                      padx=5)

        self.boton_recargar = tk.Button(
            filtros_frame, text="recargar",
            bg="#e6e6e6",
            font=("Arial", 10),
            command=self.recargar_cards,
            width=12
        )
        self.boton_recargar.pack(side="left",
                                 padx=5)

        # Separador visual
        separador = tk.Frame(self.main_frame,
                             height=2,
                             bg="#dedede",
                             bd=0,
                             relief="flat")
        separador.pack(fill="x", padx=40, pady=(0, 10))

        # Frame principal donde van las cards de funcionalidades
        self.cards_frame = tk.Frame(self.main_frame,
                                    bg="#F7F7F7")
        self.cards_frame.pack(fill="both",  
                              expand=True,
                              padx=40,
                              pady=(0, 20))

        # Lista de funcionalidades
        self.funcionalidades = [
            {
                "titulo": "Desbloquear usuario",
                "desc": "Borrar usuario de un ambiente...",
                "acceso_directo": False,
                "accion": self.usar_desbloquear_usuario
            },
            {
                "titulo": "Autorizar tablas",
                "desc": "Autoriza ciertas tablas en BD.",
                "acceso_directo": False,
                "accion": self.usar_autorizar_tablas
            },
            {
                "titulo": "Actualizar fecha de contabilidad",
                "desc": "Descripción...",
                "acceso_directo": False,
                "accion": self.usar_actualizar_fecha_cont
            }
        ]

        # Inicialmente, mostrar todas las funcionalidades
        self.mostrar_funcionalidades()

    def mostrar_funcionalidades(self, acceso_rapido=False):
        
        #Muestra las cards de funcionalidades.
        #Si acceso_rapido es True, solo muestra las cards habilitadas como acceso rápido
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Determina qué funcionalidades mostrar (todas o solo acceso rápido)
        if acceso_rapido:
            funcionalidades_a_mostrar = [f for f in self.funcionalidades if f["acceso_directo"]]

            #si no tiene funcionalidades de acceso rapido, se mostrara un mensaje
            if not funcionalidades_a_mostrar:
                mensaje = tk.Label(
                    self.cards_frame,
                    text="no tienes ningun acceso rapido activo. \nMarca alguna funcionalidad y la veras aqui", #\n = <br> 
                    font=("Arial", 12, "italic"),
                    bg="#f7f7f7",
                    fg="#212020",
                    justify="center"
                )
                mensaje.pack(expand=True, pady=50)
                return
        else:
            funcionalidades_a_mostrar = self.funcionalidades

         #filtrado por busqueda (si hay accesos rapido)
        texto = getattr(self, "texto_busqueda","")
        if texto:
            funcionalidades_a_mostrar = [
                f for f in funcionalidades_a_mostrar
                if texto in f["titulo"].lower()or texto in f["desc"].lower()
            ]

        #si no hay accesos rapidos
        if not funcionalidades_a_mostrar:
            mensaje = tk.Label(
                self.cards_frame,
                text="No se encontraron funcionalidades con relacion a la busqueda",
                font=("Arial", 12, "italic"),
                bg="#f7f7f7",
                fg="#212020",
                justify="center"
            )
            mensaje.pack(expand=True, pady=50)
            return

        columnas = 2  # Número de columnas de las cards
        fila = 0
        columna = 0
        for func in funcionalidades_a_mostrar:
            card_frame = tk.Frame(self.cards_frame, bd=1, relief="solid", bg="#f9f9f9")
            card_frame.grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            # Título
            tk.Label(card_frame, text=func["titulo"], font=("Arial", 11, "bold"), bg="#f9f9f9").pack(pady=(6, 3))
            # Descripción
            tk.Label(card_frame, text=func["desc"], font=("Arial", 9), bg="#f9f9f9").pack(pady=(0, 7), padx=11)
            # Botón acceso rápido/acceso directo
            btn_acceso = tk.Button(
                card_frame,
                text="acceso rápido" if not func["acceso_directo"] else "quitar acceso",
                font=("Arial", 8),
                width=15,
                bg="#f9f9f9" if not func["acceso_directo"] else "#FF3131",
                command=lambda f=func: self.toggle_acceso_directo(f)
            )
            btn_acceso.pack(side="left", padx=(14, 8), pady=6)
            # Botón de usar la funcionalidad
            btn_usar = Button(
                card_frame,
                text="Usar",
                command=func["accion"]
                )
            btn_usar.pack(side="right", padx=10, pady=6)

            columna += 1
            if columna >= columnas:
                columna = 0
                fila += 1


    #------------------las funciones estan desordenadas, luego me encargo de ordenarlas por seccion----

        #Funciones Frame izquierdo

    #boton salir
    def salir(self):
        self.root.destroy()
    
        #-----------------Funciones frame derecho-------------------
    
    #buscador
    def accion_busqueda(self):
        txt = self.entry_busqueda.get()
        if txt == self.placeholder_text or txt.strip() == "":
            self.texto_busqueda = ""
        else:
            self.texto_busqueda = txt.strip().lower()
        self.mostrar_funcionalidades(acceso_rapido=self.filtro_acceso_rapido)
        print("el script se ejecuto correctamente")

    def accion_busqueda(self):
        self.texto_busqueda = self.entry_busqueda.get().strip().lower()
        self.mostrar_funcionalidades(acceso_rapido=self.filtro_acceso_rapido)

        #----------------Botones de accion-----------------------
    
    #Boton de acceso rapido
    def toggle_acceso_rapido(self):
        """
        Alterna el estado del filtro de acceso rápido.
        Cambia el color del botón y muestra solo las funcionalidades correspondientes.
        """
        self.filtro_acceso_rapido = not self.filtro_acceso_rapido

        if self.filtro_acceso_rapido:
            self.boton_acceso_rapido.config(bg=self.color_boton_activo, fg="white")
            self.mostrar_funcionalidades(acceso_rapido=True)
            print("Acceso rápido habilitado",
                "Mostrando solo funcionalidades de acceso rápido.\n"
                "El botón está rojo porque el filtro está activo.")
        else:
            self.boton_acceso_rapido.config(bg=self.color_boton_default, fg="black")
            self.mostrar_funcionalidades(acceso_rapido=False)
            print("Todos los accesos",
                "Todos los elementos han sido restaurados.")
            
    def toggle_acceso_directo(self, funcionalidad):
        """
        Cambia el valor de acceso rápido en la funcionalidad y actualiza la vista.
        """
        funcionalidad["acceso_directo"] = not funcionalidad["acceso_directo"]
        # Al cambiar un acceso, vuelve a mostrar las cards conforme el filtro actual
        self.mostrar_funcionalidades(self.filtro_acceso_rapido)
            
    #Boton de Todos
    def mostrar_todos(self):
        """
        Acceso rápido: Desactiva el filtro y muestra todas las funcionalidades
        """
        self.filtro_acceso_rapido = False
        self.boton_acceso_rapido.config(bg=self.color_boton_default, fg="black")
        self.mostrar_funcionalidades(acceso_rapido=False)
        print("Todos los accesos", "Todos los elementos han sido restaurados.")

    #Boton de recarga
    def recargar_cards(self):
        
        self.entry_busqueda.delete(0, tk.END)
        self.entry_busqueda.insert(0, self.placeholder_text)
        self.entry_busqueda.config(foreground='black')
        self.texto_busqueda = ""
        self.filtro_acceso_rapido = False
        self.boton_acceso_rapido.config(bg=self.color_boton_default, fg="black")
        self.mostrar_funcionalidades(acceso_rapido=False)

        #forzar el focus
        self.entry_busqueda.focus_set()
        self.entry_busqueda.icursor(0)
        self.root.focus()

        #----------------Ventana modal-----------------------

    #configuraciones generales para la ventana modal
    def abrir_modal(self, parent, ambientes_lista, callback_confirmar):
            #creacion de la ventana modal
            modal = Toplevel(parent)
            ancho, alto = 320, 160
            modal.title("desbloquear usuario")
            self.centrar_ventana(modal, ancho, alto)
            modal.grab_set()
            modal.resizable(False, False)

            #etiqueta campo y ambiente
            lbl_ambiente = Label(modal, text="Ambiente")
            lbl_ambiente.place(x=20, y=30)
            entry_ambiente = Entry(modal)
            entry_ambiente.place(x=100, y=30, width=180)
            
    #no se descarta la idea de un autocompletado y/o una lista con todos los ambientes, por ahora dejemoslo escrito

            #etiqueta y campo de usuario
            lbl_usuario = Label(modal, text="Usuario")
            lbl_usuario.place(x=20, y=70)
            entry_usuario = Entry(modal)
            entry_usuario.place(x=100, y=70, width=180)

            def on_continuar():
                ambiente = entry_ambiente.get()
                usuario = entry_usuario.get()
                if not ambiente or not usuario: 
                    messagebox.showwarning("Campo/s vació/s", "Por favo complete ambos campos.")
                    return
                #buscar el a,biente en la lista real
                ambiente_obj = next((a for a in ambientes_lista if a['descripcion'] == ambiente), None)
                if ambiente_obj is None:
                    messagebox.showerror("Ambiente no encontrado", "Por favor complete ambos campos.")
                    return
                #llamar callback para ejecutar la accion real de desbloquear
                callback_confirmar(usuario, ambiente_obj)
                modal.destroy()
            btn_continuar = Button(modal, text="Continuar", width=12, command=on_continuar)
            btn_continuar.place(relx=1.0, rely=1.0, x=-30, y=-20, anchor='se')

        #centrar ventanas modales
    def centrar_ventana(self, ventana, ancho, alto):
        ventana.update_idletasks()
        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()
        x = int((pantalla_ancho/2)-(ancho/2))
        y = int((pantalla_alto/2)-(alto/2))
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    #botones de usar (independientes) se debe agregar uno cada vez que haya una nueva "card"
    def usar_desbloquear_usuario(self):
        self.abrir_modal(self.master, self.lista_de_ambientes, self.desbloquear_usuario_en_bd)

    def usar_autorizar_tablas(self):
        messagebox.showinfo("funcion no implementada", "esta funcion estara disponible en breve" )
    
    def usar_actualizar_fecha_cont(sefl):
        messagebox.showinfo("funcion no implementada", "esta funcion estara disponible en breve")
    
        #--------------Acciones de las ventanas modales-------------------

    #Desbloquear usuarios
    def desbloquear_usuario_en_bd(self, usuario, ambiente):
        import pyodbc
        try:
            # Ajusta con los campos que realmente tiene tu config de ambiente
            conn_str = f"DRIVER={{Adaptive Server Enterprise}};SERVER={ambiente['ip']},{ambiente['port']};DATABASE={ambiente['base_datos']};UID={ambiente['usuario']};PWD={ambiente['clave']}"
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            cursor.execute(f"sp_locklogin '{usuario}', 'unlock'")
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Usuario {usuario} desbloqueado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")