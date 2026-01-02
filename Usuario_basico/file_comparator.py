#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparador de Archivos - Aplicación con Interfaz Gráfica Moderna
Desarrollado para comparar múltiples archivos y generar reportes de diferencias
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import difflib
import os
from datetime import datetime
from pathlib import Path
import threading

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

class ModernFileComparator(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Comparador de Archivos - Versión Profesional")
        self.resizable(True, True)
        self.configure(bg='#f0f0f0')

        # --- CORRECCIÓN: Se elimina grab_set() para permitir la minimización ---
        # La ventana principal ya espera con wait_window() desde usu_basico_main.py
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Variables
        self.selected_files = []
        self.processed_file_contents = {} # Almacenar contenido procesado para el reporte
        self.original_file_contents = {}
        self.comparison_results = []
        self._is_syncing_cursor = False # Flag para evitar recursión en la sincronización
        self.summary_window_instance = None # Para rastrear la ventana de resumen
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()

    def _on_close(self):
        """Manejador para el cierre de la ventana."""
        # --- CORRECCIÓN: Traer la ventana principal al frente antes de cerrar ---
        parent = self.master
        if parent and parent.winfo_exists():
            parent.deiconify()
            parent.lift()
            parent.focus_force() # Mantenemos el foco en la ventana principal
        self.destroy()
    
    def create_interface(self):
        """Crear la interfaz gráfica principal"""
        # Frame principal
        main_frame = ttk.Frame(self, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="🔍 Comparador de Archivos Profesional",
                              font=('Segoe UI', 24, 'bold'),
                              bg='#ffffff',
                              fg='#2196F3')
        title_label.pack(pady=(0, 30))
        
        # Contenedor principal para los paneles (ahora estáticos)
        panels_container = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='#e0e0e0', sashwidth=8)
        panels_container.pack(fill=tk.BOTH, expand=True)

        # --- Panel Izquierdo (Controles) ---
        controls_frame = ttk.Frame(panels_container, padding=10)
        panels_container.add(controls_frame, width=350, minsize=300)

        # --- Panel Derecho (Resultados) ---
        results_container = ttk.Frame(panels_container, padding=10)
        panels_container.add(results_container, minsize=400)

        # --- Llenar los paneles ---
        self.create_controls_panel(controls_frame)
        self.create_results_frame(results_container)

    def create_controls_panel(self, parent):
        """Crea todo el contenido del panel de control izquierdo."""
        parent.rowconfigure(2, weight=1) # Espacio extra va al final
        parent.columnconfigure(0, weight=1)

        # Frame para selección de archivos
        self.create_file_selection_frame(parent)

        # Frame para opciones
        self.create_options_frame(parent)

        # Frame para botones de reporte y cierre (en la parte inferior)
        bottom_frame = ttk.Frame(parent)
        bottom_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        ttk.Button(bottom_frame, text="💾 Guardar Reporte", command=self.save_report, bootstyle="secondary").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(bottom_frame, text="🧹 Limpiar Resultados", command=self.clear_results, bootstyle="secondary").grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ttk.Button(bottom_frame, text="Cerrar", command=self._on_close, bootstyle="danger").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    
    def create_file_selection_frame(self, parent):
        """Crear frame para selección de archivos"""
        file_frame = ttk.LabelFrame(parent, text="📁 Selección de Archivos", 
                                   padding=(15, 10))
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        file_frame.columnconfigure(0, weight=1)
        
        # Lista de archivos seleccionados
        self.files_listbox = tk.Listbox(file_frame, 
                                       height=6, # Reducir altura para dar espacio a las opciones
                                       font=('Consolas', 10),
                                       bg='#f8f9fa',
                                       selectbackground='#2196F3',
                                       selectforeground='white', relief=tk.FLAT, borderwidth=1)
        self.files_listbox.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # --- CORRECCIÓN: Registrar el widget para Drag and Drop ---
        if DND_AVAILABLE:
            drop_text = "💡 Arrastra archivos aquí desde el explorador"
            self.files_listbox.drop_target_register(DND_FILES)
            self.files_listbox.dnd_bind('<<Drop>>', self.on_drop_files)
        else:
            drop_text = "💡 (Instala 'tkinterdnd2' para Drag & Drop)"

        tk.Label(file_frame, text=drop_text,
                 font=('Segoe UI', 9, 'italic'), fg='#666666').grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        
        # Botones de gestión de archivos
        ttk.Button(file_frame, text="➕ Agregar", command=self.add_files, bootstyle="primary-outline").grid(row=2, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(file_frame, text="🧹 Limpiar", command=self.clear_all_files, bootstyle="secondary-outline").grid(row=2, column=1, sticky="ew", padx=(5, 0))
    
    def create_options_frame(self, parent):
        """Crear frame de opciones de comparación"""
        options_frame = ttk.LabelFrame(parent, text="⚙️ Opciones de Comparación", 
                                      padding=(15, 10))
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        options_frame.columnconfigure(0, weight=1)
        
        # Variables de opciones
        self.ignore_whitespace = tk.BooleanVar(value=False)
        self.ignore_case = tk.BooleanVar(value=False)
        self.show_context = tk.BooleanVar(value=True)
        self.sync_scroll = tk.BooleanVar(value=True)
        
        # Checkboxes
        ttk.Checkbutton(options_frame, text="Ignorar espacios en blanco", variable=self.ignore_whitespace, bootstyle="round-toggle").pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Ignorar mayúsculas/minúsculas", variable=self.ignore_case, bootstyle="round-toggle").pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Mostrar contexto en diferencias", variable=self.show_context, bootstyle="round-toggle").pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Sincronizar scroll", variable=self.sync_scroll, bootstyle="round-toggle").pack(anchor=tk.W)
        
        # Botón de comparación, ahora dentro de este frame
        self.compare_button = ttk.Button(options_frame, text="🔍 COMPARAR", 
                  command=self.compare_files,
                  bootstyle="success",
                  state='disabled') # Deshabilitado inicialmente
        # Padding superior para separarlo de los checkboxes
        self.compare_button.pack(fill=tk.X, pady=(15, 0))
    
    def create_results_frame(self, parent):
        """Crear frame para mostrar resultados"""
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        results_frame = ttk.LabelFrame(parent, text="📊 Resultados de Comparación", padding=10)
        results_frame.grid(row=0, column=0, sticky="nsew")
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)

        # RF10.1: Contenedor tipo splitter horizontal
        panels_display_frame = ttk.Frame(results_frame, style='Modern.TFrame')
        panels_display_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid para que las dos columnas tengan el mismo peso
        panels_display_frame.grid_columnconfigure(0, weight=1)
        panels_display_frame.grid_columnconfigure(1, weight=1)
        panels_display_frame.grid_rowconfigure(0, weight=1) # Solo una fila

        # Panel A (Izquierda)
        frame_a = ttk.Frame(panels_display_frame)
        title_frame_a = self._create_title_frame(frame_a, "Archivo 1")
        self.title_label_a = title_frame_a['title']
        self.cursor_pos_label_a = title_frame_a['status']
        self.text_a = self._create_text_widget(frame_a, self.cursor_pos_label_a, is_left_panel=True)
        frame_a.grid(row=0, column=0, sticky="nsew") # Empaquetar con grid

        # Panel B (Derecha)
        frame_b = ttk.Frame(panels_display_frame)
        title_frame_b = self._create_title_frame(frame_b, "Archivo 2")
        self.title_label_b = title_frame_b['title']
        self.cursor_pos_label_b = title_frame_b['status']
        self.text_b = self._create_text_widget(frame_b, self.cursor_pos_label_b, is_left_panel=False)
        frame_b.grid(row=0, column=1, sticky="nsew") # Empaquetar con grid

        # RF: Crear un frame contenedor para el botón de Resumen y empaquetarlo al final de 'parent'
        summary_button_wrapper_frame = ttk.Frame(parent)
        # Este wrapper siempre estará presente en la parte inferior, reservando su espacio
        summary_button_wrapper_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.summary_button = ttk.Button(summary_button_wrapper_frame, text="📊 Ver Resumen Detallado",
                                         command=self._show_summary_window, bootstyle="info")
        self.summary_button.pack(fill=tk.X) # El botón se empaqueta dentro de su propio wrapper
        self.all_detailed_diffs = [] # --- CORRECCIÓN: Inicializar la variable que faltaba ---
        self.summary_button.pack_forget() # Ocultarlo inicialmente (solo el botón, no el wrapper)

        # Actualizar posición inicial del cursor
        self._update_cursor_position_display(self.text_a, self.cursor_pos_label_a) # type: ignore
        self._update_cursor_position_display(self.text_b, self.cursor_pos_label_b) # type: ignore

        # Sincronizar scroll
        # La configuración se hace en _create_text_widget para tener acceso a las scrollbars

        # Configurar tags para colores
        for text_widget in [self.text_a, self.text_b]:
            text_widget.tag_configure("diff", background="#FFEBEE") # Rojo claro para diferencias
            text_widget.tag_configure("diff_word", background="#F44336", foreground="white", font=('Consolas', 10, 'bold')) # Rojo intenso
            text_widget.tag_configure("sync_line", background="#E0E0E0") # Gris claro para la línea sincronizada
            text_widget.tag_configure("sync_char", background="#A9A9A9", foreground="white") # Gris oscuro para el carácter sincronizado
            text_widget.tag_configure("header", foreground="#2196F3", font=('Consolas', 10, 'bold'))

    def _create_title_frame(self, parent, initial_text):
        """Crea el frame del título con el nombre del archivo y la etiqueta de estado."""
        title_frame = ttk.Frame(parent, padding=(5, 2))
        title_frame.pack(pady=(0, 5), fill=tk.X)
        
        title_label = ttk.Label(title_frame, text=initial_text, font=('Segoe UI', 10, 'bold'), anchor='w')
        title_label.pack(side=tk.LEFT)
        
        status_label = ttk.Label(title_frame, text="Ln 1, Col 1", font=('Segoe UI', 9), anchor='e')
        status_label.pack(side=tk.RIGHT)
        
        return {'title': title_label, 'status': status_label}

    def _create_text_widget(self, parent, cursor_pos_label, is_left_panel=True):
        """Crea un widget de texto con scrollbars e indicador de posición del cursor."""
        container_frame = ttk.Frame(parent)
        container_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configurar grid para container_frame: una columna para text_frame (expansible), otra para diff_map (ancho fijo)
        container_frame.grid_columnconfigure(0, weight=1) # Columna para text_frame
        container_frame.grid_columnconfigure(1, weight=0) # Columna para diff_map (ancho fijo)
        container_frame.grid_rowconfigure(0, weight=1) # Solo una fila para el contenido principal

        # Frame para el texto y sus scrollbars
        text_frame = ttk.Frame(container_frame, relief=tk.GROOVE, borderwidth=1)
        text_frame.grid(row=0, column=0, sticky="nsew") # Colocar text_frame en la primera columna
        text = tk.Text(text_frame, wrap=tk.NONE, font=('Consolas', 10), 
                       bg='#fdfdfd', borderwidth=0, highlightthickness=0)
        
        # Asignar el comando de scroll correcto para la sincronización
        # La sincronización se maneja a través de los comandos de las scrollbars
        # --- CORRECCIÓN: Asignar comandos de scroll para ambos ejes ---
        scroll_command_y = self._on_scroll_a_y if is_left_panel else self._on_scroll_b_y
        scroll_command_x = self._on_scroll_a_x if is_left_panel else self._on_scroll_b_x
        
        # --- MEJORA: Añadir contador de líneas a AMBOS paneles ---
        line_numbers_canvas = tk.Canvas(text_frame, width=40, bg='#f0f0f0', highlightthickness=0)
        
        # Crear un nuevo comando de scroll que actualice los números de línea
        def yscroll_with_linenumbers(*args):
            scroll_command_y(*args)
            self._update_line_numbers()
        
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=yscroll_with_linenumbers)
        text.config(yscrollcommand=v_scroll.set)

        if is_left_panel:
            self.line_numbers_a = line_numbers_canvas
        else:
            self.line_numbers_b = line_numbers_canvas
        
        h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=scroll_command_x)
        text.config(xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X) 
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 

        # Empaquetar el contador de líneas al principio (izquierda)
        line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y, before=text)
        
        # Ocultar el contador derecho por defecto
        if not is_left_panel:
            line_numbers_canvas.pack_forget()

        # Bind events to update cursor position display
        # --- CORRECCIÓN: Separar la actualización de la UI de la sincronización ---
        text.bind("<KeyRelease>", lambda event, t=text, l=cursor_pos_label: self._on_ui_change(event, t, l), add='+')
        text.bind("<Button-1>", lambda event, t=text, l=cursor_pos_label: self._on_ui_change(event, t, l), add='+')
        # --- CORRECCIÓN: Permitir teclas de navegación pero bloquear edición ---
        text.bind("<KeyPress>", self._on_key_press)

        text.bind("<MouseWheel>", self._on_mouse_wheel) # Para Windows y macOS
        text.bind("<Button-4>", self._on_mouse_wheel)   # Para Linux (scroll up)
        text.bind("<Button-5>", self._on_mouse_wheel)   # Para Linux (scroll down)
        text.bind("<Shift-MouseWheel>", self._on_horizontal_mouse_wheel) # Scroll horizontal
        
        # Barra de marcadores de diferencias (Diff Map)
        diff_map = tk.Canvas(container_frame, width=15, bg='#e0e0e0', highlightthickness=0)
        diff_map.grid(row=0, column=1, sticky="nsew", padx=(2, 0)) # Colocar diff_map en la segunda columna
        diff_map.bind("<Button-1>", lambda event: self._on_marker_click(event, diff_map))

        # Asignar a atributos de la clase
        if is_left_panel:
            self.diff_map_a = diff_map
        else:
            self.diff_map_b = diff_map

        
        return text

    def _on_key_press(self, event):
        """
        Manejador de pulsación de teclas.
        Permite el paso de teclas de navegación, la acción de copiar (Ctrl+C),
        y bloquea las de edición.
        """
        # Lista de teclas de navegación permitidas
        allowed_keys = ['Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End']

        # Permitir Ctrl+C (o Command+C en macOS) para copiar.
        # El bit 4 en event.state corresponde a la tecla Control.
        if (event.state & 4) and event.keysym.lower() == 'c':
            return # Permitir que el evento de copia continúe

        if event.keysym in allowed_keys:
            return  # No hacer nada, permitir que el evento continúe
        return "break"  # Bloquear cualquier otra tecla

    def _update_line_numbers(self, *args):
        """Actualiza el canvas del contador de líneas."""
        # --- MEJORA: Actualizar ambos contadores de línea ---
        if not hasattr(self, 'line_numbers_a') or not hasattr(self, 'line_numbers_b'):
            return

        # Limpiar ambos canvas
        self.line_numbers_a.delete("all")
        self.line_numbers_b.delete("all")
        
        # Crear conjuntos de líneas con diferencias
        diff_lines_a = set()
        diff_lines_b = set()
        if hasattr(self, 'all_detailed_diffs') and self.all_detailed_diffs:
            for diff in self.all_detailed_diffs:
                if diff['file1_line_num'] != "N/A":
                    diff_lines_a.add(diff['file1_line_num'])
                if diff['file2_line_num'] != "N/A":
                    diff_lines_b.add(diff['file2_line_num'])
        
        # Usar text_a como referencia, ya que están sincronizados
        try:
            first_visible_line_index = self.text_a.index("@0,0")
            
            # Iterar sobre las líneas visibles y dibujar los números en ambos canvas
            i = self.text_a.index(f"{first_visible_line_index} linestart")
            while True:
                dline = self.text_a.dlineinfo(i)
                if dline is None: break
                y = dline[1]
                linenum_str = str(i).split('.')[0]
                linenum_int = int(linenum_str)
                
                # Determinar color según si la línea tiene diferencias
                color_a = '#F44336' if linenum_int in diff_lines_a else '#666'
                color_b = '#F44336' if linenum_int in diff_lines_b else '#666'
                
                # Dibujar en ambos
                self.line_numbers_a.create_text(20, y, anchor="n", text=linenum_str, font=('Consolas', 10, 'bold' if linenum_int in diff_lines_a else 'normal'), fill=color_a)
                self.line_numbers_b.create_text(20, y, anchor="n", text=linenum_str, font=('Consolas', 10, 'bold' if linenum_int in diff_lines_b else 'normal'), fill=color_b)
                
                i = self.text_a.index(f"{i}+1line")
        except tk.TclError:
            # Puede ocurrir si el widget se destruye mientras se actualiza
            pass

    def _on_ui_change(self, event, source_widget, status_label):
        """Manejador para eventos de UI que actualiza la etiqueta y sincroniza el cursor."""
        # --- SOLUCIÓN DEFINITIVA: Dar foco y separar la lógica de sincronización ---
        source_widget.focus_set()

        # --- MEJORA: Mostrar el contador de líneas del panel activo ---
        is_left = source_widget == self.text_a
        self.line_numbers_a.pack(side=tk.LEFT, fill=tk.Y, before=self.text_a) if is_left else self.line_numbers_a.pack_forget()
        self.line_numbers_b.pack(side=tk.LEFT, fill=tk.Y, before=self.text_b) if not is_left else self.line_numbers_b.pack_forget()

        if self.sync_scroll.get():
            # Si la sincronización está activa, programar la sincronización completa.
            self.after_idle(lambda: self._sincronizar_cursor(source_widget))
        else:
            # Si está desactivada, solo actualizar la etiqueta del panel actual.
            # Usamos after_idle para asegurar que leemos la posición del cursor después del clic.
            self.after_idle(lambda: self._update_cursor_position_display(source_widget, status_label))
        
        # Actualizar siempre los números de línea después de un cambio
        self.after_idle(self._update_line_numbers)

    def _sincronizar_cursor(self, source_widget):
        """Sincroniza la posición del cursor del widget de origen al de destino."""
        if not self.sync_scroll.get():
            return

        try:
            if self._is_syncing_cursor:
                return
            self._is_syncing_cursor = True
            
            is_left = source_widget == self.text_a
            # --- CORRECCIÓN: Identificar el widget y la etiqueta de destino ---
            target_widget = self.text_b if is_left else self.text_a
            target_label = self.cursor_pos_label_b if is_left else self.cursor_pos_label_a
            source_label = self.cursor_pos_label_a if is_left else self.cursor_pos_label_b

            # --- SOLUCIÓN DEFINITIVA: Sincronizar la vista y luego el cursor ---
            self._sincronizar_vistas(source_widget)

            current_cursor_pos = source_widget.index(tk.INSERT)
            target_widget.mark_set(tk.INSERT, current_cursor_pos)

            # --- SOLUCIÓN: Limpiar marcas anteriores y resaltar el carácter en el panel de destino ---
            self.text_a.tag_remove("sync_char", "1.0", "end")
            self.text_b.tag_remove("sync_char", "1.0", "end")
            char_end = f"{current_cursor_pos}+1c"
            target_widget.tag_add("sync_char", current_cursor_pos, char_end)
            
            # --- CORRECCIÓN: Actualizar AMBAS etiquetas después de la sincronización ---
            self._update_cursor_position_display(source_widget, source_label) # type: ignore
            self._update_cursor_position_display(target_widget, target_label) # type: ignore
        finally:
            self.after_idle(lambda: setattr(self, '_is_syncing_cursor', False))

    def _sincronizar_vistas(self, source_widget):
        """Función central para sincronizar las vistas de ambos paneles."""
        yview_pos = source_widget.yview()
        xview_pos = source_widget.xview()
        self.text_a.yview_moveto(yview_pos[0])
        self.text_b.yview_moveto(yview_pos[0])
        self.text_a.xview_moveto(xview_pos[0])
        self.text_b.xview_moveto(xview_pos[0])

    def _update_cursor_position_display(self, text_widget, label_widget):
        """Actualiza la etiqueta con la posición actual del cursor (línea y carácter)."""
        try:
            cursor_index = text_widget.index(tk.INSERT)
            line, char = map(int, cursor_index.split('.'))
            label_widget.config(text=f"Ln {line}, Col {char + 1}")
        except tk.TclError:
            # Esto puede ocurrir si el widget no está completamente inicializado o está vacío.
            label_widget.config(text="Ln ?, Col ?")

    def _on_scroll_a_y(self, *args):
        """Maneja el scroll vertical del panel A y sincroniza con B."""
        # args son (fraction_start, fraction_end) del scrollbar.set
        if self.sync_scroll.get():
            # Aplicar la acción de scroll a ambos paneles.
            # El método yview del Text widget interpreta correctamente todos los tipos de *args del scrollbar.
            self.text_a.yview(*args) # Esto es idempotente, pero asegura que el panel A se mueva.
            self.text_b.yview(*args) # Sincroniza el panel B con la misma acción.
        else:
            # Solo mover el panel A
            self.text_a.yview(*args)

        self.after_idle(self._update_line_numbers)
    def _on_scroll_b_y(self, *args):
        """Maneja el scroll vertical del panel B y sincroniza con A."""
        # --- CORRECCIÓN: Implementar la sincronización para el panel B ---
        if self.sync_scroll.get():
            # Aplicar la acción de scroll a ambos paneles.
            self.text_b.yview(*args)
            self.text_a.yview(*args)
        else:
            self.text_b.yview(*args)
        self.after_idle(self._update_line_numbers)

    def _on_scroll_a_x(self, *args):
        """Maneja el scroll horizontal del panel A y sincroniza con B."""
        # --- CORRECCIÓN: Implementar sincronización horizontal ---
        if self.sync_scroll.get():
            self.text_a.xview(*args)
            self.text_b.xview(*args)
        else:
            self.text_a.xview(*args)

    def _on_scroll_b_x(self, *args):
        """Maneja el scroll horizontal del panel B y sincroniza con A."""
        # --- CORRECCIÓN: Implementar sincronización horizontal ---
        if self.sync_scroll.get():
            self.text_b.xview(*args)
            self.text_a.xview(*args)
        else:
            self.text_b.xview(*args)

    def _on_mouse_wheel(self, event):
        """Maneja el scroll con la rueda del mouse y sincroniza ambos paneles si la opción está activa."""
        if self.sync_scroll.get():
            # Determinar la dirección del scroll para compatibilidad entre plataformas
            if event.num == 5 or event.delta < 0:
                scroll_units = 2  # Scroll hacia abajo
            else:
                scroll_units = -2 # Scroll hacia arriba
            
            # Aplicar el scroll a ambos paneles
            self.text_a.yview_scroll(scroll_units, "units")
            self.text_b.yview_scroll(scroll_units, "units")
            
            # Actualizar números de línea
            self.after_idle(self._update_line_numbers)

            # Devolver "break" para evitar que el evento se propague y cause un doble scroll
            return "break"

    def _on_horizontal_mouse_wheel(self, event):
        """Maneja el scroll horizontal con la rueda del mouse (Shift + Rueda) y sincroniza."""
        if self.sync_scroll.get():
            if event.delta > 0:
                scroll_units = -2 # Scroll hacia la izquierda
            else:
                scroll_units = 2  # Scroll hacia la derecha
            
            self.text_a.xview_scroll(scroll_units, "units")
            self.text_b.xview_scroll(scroll_units, "units")
            return "break"

    def center_window(self):
        """Centrar la ventana en la pantalla"""
        self.update_idletasks()
        # Definir un tamaño inicial razonable (ej. 80% del ancho, 75% del alto)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.85) # Aumentar altura inicial
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2) - 40 # Subir la ventana 50px
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def add_files(self):
        """Agregar archivos para comparar"""
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos para comparar",
            filetypes=[
                ("Archivos de salida", "*.out *.output *.result"),
                ("Archivos de texto", "*.txt *.log *.csv *.json *.xml *.properties"),
                ("Archivos de código", "*.py *.java *.js *.html *.css *.sql"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
        self._update_compare_button_state()
    
    def on_drop_files(self, event):
        """Manejar archivos arrastrados desde el explorador"""
        if DND_AVAILABLE:
            files = self.tk.splitlist(event.data)
        else:
            return
        
        added_count = 0
        for file_path in files:
            if os.path.isfile(file_path) and file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.files_listbox.insert(tk.END, os.path.basename(file_path))
                added_count += 1
        self._update_compare_button_state()
    
    def remove_selected_file(self):
        """Eliminar archivo seleccionado"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            # Eliminar de la lista de archivos seleccionados
            del self.selected_files[index]
            # Eliminar del listbox
            self.files_listbox.delete(index)
        self._update_compare_button_state()
    
    def clear_all_files(self):
        """Limpiar todos los archivos"""
        self.files_listbox.delete(0, tk.END)
        self.selected_files.clear()
        self.processed_file_contents.clear()
        self.original_file_contents.clear()
        # Limpiar también los resultados de la comparación
        self.clear_results()
        self._update_compare_button_state()
    
    def clear_results(self):
        """Limpiar resultados"""
        self.comparison_results.clear()
        for widget in [self.text_a, self.text_b]:
            widget.config(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.config(state=tk.DISABLED)
        # Limpiar indicadores de cursor
        self.cursor_pos_label_a.config(text="Ln 1, Col 1") # type: ignore
        self.cursor_pos_label_b.config(text="Ln 1, Col 1") # type: ignore
        self.title_label_a.config(text="Archivo 1") # type: ignore
        self.title_label_b.config(text="Archivo 2") # type: ignore
        
        self.summary_button.pack_forget() # Ocultar el botón de resumen al limpiar
    
    def compare_files(self):
        """Comparar archivos seleccionados"""
        if len(self.selected_files) < 2:
            messagebox.showwarning("Advertencia",
                                 "Selecciona al menos 2 archivos para comparar")
            return
        
        self.compare_button.config(state='disabled') # Deshabilitar durante la comparación
        # Limpiar resultados anteriores
        self.clear_results()
        
        # Mostrar mensaje de procesamiento
        for widget in [self.text_a, self.text_b]:
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, "🔄 Procesando comparación...\n")
            widget.config(state=tk.DISABLED)
        self.update()
        
        # Ejecutar comparación en hilo separado
        thread = threading.Thread(target=self._perform_comparison)
        thread.daemon = True
        thread.start()
    
    def _perform_comparison(self):
        """Realizar la comparación de archivos"""
        # RF2: Crear la carpeta C:\zetaOne\comparador si no existe
        output_dir = Path("C:/zetaOne/comparador")
        output_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        
        try:
            self.comparison_results.clear()
            self.processed_file_contents.clear()
            self.original_file_contents.clear()
            # Leer y pre-procesar contenido de archivos
            file_contents = {}
            for file_path in self.selected_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines() # splitlines() es más robusto
                        self.original_file_contents[file_path] = lines
                        
                        processed_content = content
                        if self.ignore_case.get():
                            processed_content = processed_content.lower()
                        if self.ignore_whitespace.get():
                            # Procesar cada línea individualmente para mantener el número de líneas
                            processed_content = '\n'.join(line.strip() for line in lines)
                        
                        processed_lines = processed_content.splitlines()
                        file_contents[file_path] = processed_lines
                        self.processed_file_contents[file_path] = processed_lines # Store processed content for UI
                except Exception as e:
                    error_msg = f"❌ Error leyendo {os.path.basename(file_path)}: {str(e)}\n"
                    self.after(0, lambda msg=error_msg: self.text_a.insert(tk.END, msg))

                    continue
            
            # Comparar archivos de a pares
            # Asegurarse de que solo se comparan archivos que se pudieron leer
            for i, file1_path in enumerate(self.selected_files):
                for j, file2_path in enumerate(self.selected_files[i+1:], i+1):
                    if file1_path in file_contents and file2_path in file_contents:
                        self._compare_pair(file1_path, file2_path, 
                                           file_contents[file1_path], 
                                           file_contents[file2_path])
            # Mostrar resumen
            self.after(0, self._finalize_comparison)
            
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Error", f"Error durante la comparación: {str(err)}"))
    
    def _compare_pair(self, file1_path, file2_path, content1_processed, content2_processed):
        """Comparar un par de archivos"""
        name1 = os.path.basename(file1_path)
        name2 = os.path.basename(file2_path)
        
        # Usar SequenceMatcher para obtener opcodes, que es más útil para la vista de dos paneles
        # El parámetro 'isjunk' ayuda a ignorar líneas que no aportan información (como líneas vacías)
        # para evitar que se desincronice el comparador.
        is_junk = None
        if self.ignore_whitespace.get():
            is_junk = lambda x: not x.strip()

        matcher = difflib.SequenceMatcher(is_junk, a=content1_processed, b=content2_processed)
        
        final_opcodes = list(matcher.get_opcodes())
        has_differences = matcher.ratio() < 1.0
        
        # Almacenar resultados
        comparison_result = {
            'file1': file1_path,
            'file2': file2_path,
            'opcodes': final_opcodes,
            'has_differences': has_differences
        }
        self.comparison_results.append(comparison_result)
        
        # Mostrar resultados en la interfaz
        # La visualización se hará una vez para el primer par comparado
        if len(self.comparison_results) == 1:
            self.after(0, lambda: self._display_comparison(comparison_result))
    
    def _display_comparison(self, result):
        """Mostrar comparación en la interfaz"""
        # La visualización se hará una vez para el primer par comparado
        if len(self.comparison_results) == 1:
            first_result = self.comparison_results[0]
            
            # Usar el contenido original para mostrar en la UI
            content1 = self.original_file_contents.get(first_result['file1'], [])
            content2 = self.original_file_contents.get(first_result['file2'], [])
            
            opcodes = first_result['opcodes']
            
            # --- CORRECCIÓN: Actualizar los títulos de los paneles ---
            name1 = os.path.basename(first_result['file1'])
            name2 = os.path.basename(first_result['file2'])
            self.title_label_a.config(text=name1) # type: ignore
            self.title_label_b.config(text=name2) # type: ignore

            # Limpiar y habilitar paneles
            for widget in [self.text_a, self.text_b]:
                widget.config(state=tk.NORMAL)
                widget.delete(1.0, tk.END)

            # Poblar paneles y resaltar diferencias
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    # Mostrar las líneas idénticas
                    self.text_a.insert(tk.END, '\n'.join(content1[i1:i2]) + '\n')
                    self.text_b.insert(tk.END, '\n'.join(content2[j1:j2]) + '\n')
                
                elif tag == 'replace':
                    # Diferencia a nivel de palabra para reemplazos
                    num_lines = max(i2 - i1, j2 - j1)
                    for i in range(num_lines):
                        # Obtener líneas para mostrar y para comparar
                        line1_to_show = content1[i1 + i] if i1 + i < i2 else ""
                        line2_to_show = content2[j1 + i] if j1 + i < j2 else ""
                        
                        # Usar el contenido procesado para la comparación de caracteres
                        proc_content1 = self.processed_file_contents.get(first_result['file1'], [])
                        proc_content2 = self.processed_file_contents.get(first_result['file2'], [])
                        proc_line1 = proc_content1[i1 + i] if i1 + i < len(proc_content1) else ""
                        proc_line2 = proc_content2[j1 + i] if j1 + i < len(proc_content2) else ""
                        
                        self._highlight_char_diffs(line1_to_show, proc_line1, line2_to_show, proc_line2)
                elif tag == 'delete':
                    # Líneas eliminadas en el archivo 1
                    for i in range(i1, i2):
                        self.text_a.insert(tk.END, content1[i] + '\n', ('diff', 'diff_word'))
                        self.text_b.insert(tk.END, '\n', 'diff')
                elif tag == 'insert':
                    # Líneas insertadas en el archivo 2
                    for j in range(j1, j2):
                        self.text_a.insert(tk.END, '\n', 'diff')
                        self.text_b.insert(tk.END, content2[j] + '\n', ('diff', 'diff_word'))

            # Deshabilitar edición
            # --- CORRECCIÓN: Dejar en estado NORMAL para permitir foco y cursor, pero bloquear edición con <KeyPress> ---
            for widget in [self.text_a, self.text_b]:
                widget.config(state=tk.NORMAL)
            
            # --- CORRECCIÓN: Asegurar que ambos paneles comiencen desde el inicio ---
            self.text_a.yview_moveto(0.0)
            self.text_b.yview_moveto(0.0)
            self.text_a.xview_moveto(0.0)
            self.text_b.xview_moveto(0.0)
            
            # --- NUEVO: Actualizar los números de línea después de cargar el contenido ---
            self.after_idle(self._update_line_numbers)

    def _highlight_char_diffs(self, line1_to_show, processed_line1, line2_to_show, processed_line2):
        """
        Compara dos líneas carácter por carácter y resalta las diferencias exactas.
        """
        # 1. Insertar las líneas y aplicar el resaltado de fondo claro a toda la línea
        self.text_a.insert(tk.END, line1_to_show + '\n', 'diff')
        self.text_b.insert(tk.END, line2_to_show + '\n', 'diff')

        # 2. Obtener la posición de la línea recién insertada (es la penúltima)
        line_num_a = self.text_a.index('end-2l').split('.')[0]
        line_num_b = self.text_b.index('end-2l').split('.')[0]

        # --- MEJORA: Lógica de comparación posicional carácter por carácter ---
        # En lugar de usar difflib, se compara cada carácter en la misma posición.
        len1 = len(processed_line1)
        len2 = len(processed_line2)
        max_len = max(len1, len2)

        for i in range(max_len):
            char1 = processed_line1[i] if i < len1 else None
            char2 = processed_line2[i] if i < len2 else None

            # Si los caracteres son diferentes o uno no existe (líneas de diferente longitud),
            # se resalta el carácter en esa posición en ambos paneles.
            if char1 != char2:
                if i < len1:
                    start = f"{line_num_a}.{i}"
                    end = f"{line_num_a}.{i+1}"
                    self.text_a.tag_add("diff_word", start, end)
                if i < len2:
                    start = f"{line_num_b}.{i}"
                    end = f"{line_num_b}.{i+1}"
                    self.text_b.tag_add("diff_word", start, end)

    def _finalize_comparison(self):
        """Mostrar resumen final y generar reporte."""
        # --- CORRECCIÓN: Generar diferencias detalladas para el resumen ---
        if self.comparison_results:
            first_comparison = self.comparison_results[0]
            file1_path = first_comparison['file1']
            file2_path = first_comparison['file2']
            matcher = difflib.SequenceMatcher(None, self.processed_file_contents[file1_path], self.processed_file_contents[file2_path])
            matcher.a_name = file1_path
            matcher.b_name = file2_path
            self.all_detailed_diffs = self._generate_detailed_diff_entries(matcher, self.original_file_contents[file1_path], self.original_file_contents[file2_path])

        # Al finalizar, asegurar que la vista de ambos paneles esté al inicio.
        self.text_a.yview_moveto(0.0)
        self.text_b.yview_moveto(0.0)

        self.compare_button.config(state='normal') # Habilitar de nuevo
        self.summary_button.pack(fill=tk.X) # --- CORRECCIÓN: Mostrar el botón de resumen ---

        # Generar reporte automáticamente al finalizar
        if self.comparison_results:
            self.save_report()
    
    def save_report(self):
        """Guardar reporte de diferencias"""
        if not self.comparison_results:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar", parent=self)
            return
        
        if len(self.selected_files) < 2:
            messagebox.showwarning("Advertencia", "Se requieren al menos dos archivos para generar un reporte detallado.", parent=self)
            return
        
        # RF2: Asegurar que la carpeta C:\comparador existe
        output_dir = Path("C:/ZetaOne/comparador")
        output_dir.mkdir(parents=True, exist_ok=True) # Asegura que la carpeta existe
        
        # RF3: Nombre del archivo determinístico
        if not self.selected_files:
            messagebox.showerror("Error", "No hay archivos seleccionados para determinar el nombre del reporte.", parent=self)
            return
        # RF3: Nombre del archivo determinístico
        first_file_name_base = os.path.basename(self.selected_files[0]).split('.')[0]
        report_filename = output_dir / f"resCompara_{first_file_name_base}.txt"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # RF4, RF5: ENCABEZADO (metadatos)
                f.write("BEGIN INFORME\n")
                f.write("ENCABEZADO\n")
                f.write(f"FECHA_PROCESO: {now}\n")
                f.write(f"FECHA_EJECUCION: {now}\n")
                
                # Para el reporte determinístico, tomaremos el primer par de la comparación si existe.
                if self.comparison_results:
                    first_comparison = self.comparison_results[0]
                    file1_path = first_comparison['file1']
                    file2_path = first_comparison['file2']
                    name1 = os.path.basename(file1_path)
                    name2 = os.path.basename(file2_path)
                    
                    f.write(f"PRIMER_ARCHIVO: {name1}\n")
                    f.write(f"SEGUNDO_ARCHIVO: {name2}\n")
                    f.write("\n")
                    
                    # RF4, RF5: RESUMEN EJECUTIVO
                    f.write("RESUMEN EJECUTIVO\n")
                    
                    content1_processed = self.processed_file_contents.get(file1_path, [])
                    content2_processed = self.processed_file_contents.get(file2_path, [])

                    content1_original = self.original_file_contents.get(file1_path, [])
                    content2_original = self.original_file_contents.get(file2_path, [])
                    
                    total_lines_file1 = len(content1_original)
                    total_lines_file2 = len(content2_original)
                    
                    # --- CORRECCIÓN: Usar la lista de diferencias filtradas para el conteo total ---
                    diff_count = len(self.all_detailed_diffs)
                    f.write(f"Total líneas Archivo1: {total_lines_file1}\n") # type: ignore
                    f.write(f"Total líneas Archivo2: {total_lines_file2}\n")
                    f.write(f"DIFERENCIAS: {diff_count}\n")
                    f.write("Notas: Diferencias encontradas en el contenido de los archivos.\n")
                    f.write("\n")

                    # RF: NUEVA SECCIÓN - RESUMEN DE TIPOS DE DIFERENCIA
                    f.write("RESUMEN DE TIPOS DE DIFERENCIA (Basado en el primer par comparado)\n")
                    # --- CORRECCIÓN: La función ya no necesita 'matcher' ni los contenidos, usa 'self.all_detailed_diffs' ---
                    diff_summary = self._calculate_diff_summary(None, None, None)
                    f.write(f"Líneas agregadas: {diff_summary['lineas_agregadas']}\n")
                    f.write(f"Líneas eliminadas: {diff_summary['lineas_eliminadas']}\n")
                    f.write(f"Modificaciones de fecha: {diff_summary['reemplazos_fecha']}\n")
                    f.write(f"Modificaciones de espaciado: {diff_summary['reemplazos_espacios']}\n")
                    f.write(f"Otras modificaciones de contenido: {diff_summary['reemplazos_otro']}\n")
                    f.write("\n")
                    
                    try:
                        size1_bytes = os.path.getsize(file1_path)
                        size2_bytes = os.path.getsize(file2_path)
                        f.write(f"Tamaño Archivo1: {size1_bytes / 1024:.2f} KB\n")
                        f.write(f"Tamaño Archivo2: {size2_bytes / 1024:.2f} KB\n")
                    except OSError:
                        f.write("Tamaño Archivo1: No disponible\n")
                        f.write("Tamaño Archivo2: No disponible\n")
                    f.write("\n")
                    
                    # RF4, RF5: DETALLE DE DIFERENCIAS
                    f.write("DETALLE DE DIFERENCIAS\n")
                    
                    # --- CORRECCIÓN: Usar self.all_detailed_diffs como fuente única de verdad ---
                    if not self.all_detailed_diffs:
                        f.write("No se encontraron diferencias.\n")
                    else:
                        for diff in self.all_detailed_diffs:
                            f.write(f"\n--- Diferencia en Archivo1 (Línea {diff['file1_line_num']}) / Archivo2 (Línea {diff['file2_line_num']}) ---\n")
                            if diff['opcode'] == 'replace':
                                f.write(f"TIPO: Modificación ({diff['type']})\n")
                                f.write(f"ARCHIVO1: \"{diff['file1_content']}\"\n")
                                f.write(f"ARCHIVO2: \"{diff['file2_content']}\"\n")
                            elif diff['opcode'] == 'delete':
                                f.write("TIPO: Línea eliminada\n")
                                f.write(f"ARCHIVO1: \"{diff['file1_content']}\"\n")
                                f.write("ARCHIVO2: \"\"\n")
                            elif diff['opcode'] == 'insert':
                                f.write("TIPO: Línea agregada\n")
                                f.write("ARCHIVO1: \"\"\n")
                                f.write(f"ARCHIVO2: \"{diff['file2_content']}\"\n")

                else:
                    f.write("No se pudieron obtener los contenidos de los archivos para el reporte detallado.\n")
                
                f.write("\nFIN DEL INFORME\n")
            
            messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en:\n{report_filename}", parent=self)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el reporte: {str(e)}", parent=self)

    def _generate_detailed_diff_entries(self, matcher, content1_original, content2_original):
        """
        Genera una lista de diccionarios, cada uno representando una diferencia detallada
        a nivel de línea, incluyendo información de diferencias a nivel de carácter para reemplazos.
        """
        detailed_diffs = []

        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'replace':
                for k_line in range(max(i2 - i1, j2 - j1)):
                    line1 = content1_original[i1 + k_line] if (i1 + k_line) < i2 else ""
                    line2 = content2_original[j1 + k_line] if (j1 + k_line) < j2 else ""
                    
                    # --- Solución Definitiva: Post-filtrado ---
                    # Si las líneas procesadas son idénticas, no es una diferencia real, pero solo si la opción de ignorar está activa.
                    # Validar que los índices estén dentro del rango antes de acceder
                    idx_a = i1 + k_line
                    idx_b = j1 + k_line
                    if (idx_a < len(self.processed_file_contents[matcher.a_name]) and 
                        idx_b < len(self.processed_file_contents[matcher.b_name]) and
                        self.processed_file_contents[matcher.a_name][idx_a] == self.processed_file_contents[matcher.b_name][idx_b]):
                        continue

                    diff_type = self._classify_difference(line1, line2)
                    char_diff_info = []
                    char_matcher = difflib.SequenceMatcher(None, line1, line2)
                    for tag_char, c1_start, c1_end, c2_start, c2_end in char_matcher.get_opcodes():
                        if tag_char != 'equal':
                            char_diff_info.append({
                                'tag': tag_char,
                                'file1_char_start': c1_start,
                                'file1_char_end': c1_end,
                                'file2_char_start': c2_start,
                                'file2_char_end': c2_end
                            })

                    detailed_diffs.append({
                        'type': diff_type,
                        'opcode': opcode,
                        'file1_line_num': i1 + k_line + 1 if (i1 + k_line) < i2 else "N/A",
                        'file2_line_num': j1 + k_line + 1 if (j1 + k_line) < j2 else "N/A",
                        'file1_content': line1,
                        'file2_content': line2,
                        'char_diff_info': char_diff_info
                    })

            elif opcode == 'delete':
                for k_line in range(i1, i2):
                    detailed_diffs.append({
                        'type': 'eliminada',
                        'opcode': opcode,
                        'file1_line_num': k_line + 1,
                        'file2_line_num': "N/A",
                        'file1_content': content1_original[k_line],
                        'file2_content': "",
                        'char_diff_info': []
                    })
            elif opcode == 'insert':
                for k_line in range(j1, j2):
                    detailed_diffs.append({
                        'type': 'agregada',
                        'opcode': opcode,
                        'file1_line_num': "N/A",
                        'file2_line_num': k_line + 1,
                        'file1_content': "", # No content in file1 for an insert
                        'file2_content': "", # No content in file1 for an insert
                        'char_diff_info': []
                    })
        return detailed_diffs

    def _calculate_diff_summary(self, matcher, content1_original, content2_original): # This method is for the report
        """Calcula un resumen de los tipos de diferencias encontradas."""
        summary = {
            # --- CORRECCIÓN: Inicializar todas las claves para evitar KeyError ---
            'reemplazos_fecha': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'replace' and d['type'] == 'fecha'),
            'reemplazos_espacios': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'replace' and d['type'] == 'espacios'),
            'reemplazos_otro': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'replace' and d['type'] == 'otro'),
            'lineas_agregadas': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'insert'),
            'lineas_eliminadas': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'delete'),
        }
        return summary

    def _classify_difference(self, line1, line2):
        """
        Clasifica el tipo de diferencia entre dos líneas.
        Utiliza heurísticas para identificar si es una diferencia de fecha, espaciado u otra.
        Retorna 'fecha', 'espacios', 'otro'.
        """
        import re

        # Heurística 1: Diferencia de espaciado
        if line1.strip() == line2.strip() and line1 != line2:
            return 'espacios'

        # Heurística 2: Diferencia de fecha
        date_regex = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        
        # Buscar fechas en ambas líneas
        dates1 = re.findall(date_regex, line1)
        dates2 = re.findall(date_regex, line2)

        # Si encontramos al menos una fecha en cada línea y son diferentes, lo clasificamos como fecha
        if dates1 and dates2 and dates1 != dates2:
            return 'fecha'

        return 'otro'

    def _show_summary_window(self):
        """Muestra una nueva ventana con el resumen detallado de las diferencias."""
        if not self.all_detailed_diffs:
            messagebox.showinfo("Resumen", "No hay diferencias para mostrar en el resumen.", parent=self)
            return

        # --- CORRECCIÓN: Evitar abrir múltiples ventanas de resumen ---
        if self.summary_window_instance and self.summary_window_instance.winfo_exists():
            self.summary_window_instance.deiconify() # Restaurar si está minimizada
            self.summary_window_instance.lift()
            self.summary_window_instance.focus_force()
            return
        # -------------------------------------------------------------

        # --- CORRECCIÓN: La ventana de resumen debe ser hija de la ventana del comparador (self) ---
        # --- OPTIMIZACIÓN: Asignar nombres al matcher aquí, una sola vez ---
        first_comparison = self.comparison_results[0]
        matcher = difflib.SequenceMatcher(None, self.processed_file_contents[first_comparison['file1']], self.processed_file_contents[first_comparison['file2']])
        matcher.a_name = first_comparison['file1']
        matcher.b_name = first_comparison['file2']
        self.all_detailed_diffs = self._generate_detailed_diff_entries(matcher, self.original_file_contents[matcher.a_name], self.original_file_contents[matcher.b_name])

        summary_window = tk.Toplevel(self)
        self.summary_window_instance = summary_window # Guardar la instancia
        summary_window.title("Resumen de Diferencias Detallado")
        summary_window.configure(bg='#f0f0f0')
        summary_window.resizable(True, True)
        # summary_window.grab_set() # Se elimina para permitir la minimización

        # Centrar la ventana de resumen y darle un tamaño proporcional
        summary_window.update_idletasks()
        screen_width = summary_window.winfo_screenwidth()
        screen_height = summary_window.winfo_screenheight()
        width = int(screen_width * 0.75)
        height = int(screen_height * 0.75)
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        summary_window.geometry(f'{width}x{height}+{x}+{y}')

        # Frame para los botones de resumen por tipo
        summary_counts_frame = ttk.LabelFrame(summary_window, text="Resumen por Tipo", padding=10)
        summary_counts_frame.pack(fill=tk.X, padx=10, pady=5)

        # Calcular los conteos de resumen a partir de self.all_detailed_diffs
        current_summary_counts = {
            'reemplazos_fecha': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'replace' and d['type'] == 'fecha'),
            'reemplazos_espacios': sum(1 for d in self.all_detailed_diffs if d['opcode'] == 'replace' and d['type'] == 'espacios'),
            'reemplazos_otro': 0,
            'lineas_agregadas': 0,
            'lineas_eliminadas': 0,
        }
        for diff in self.all_detailed_diffs:
            if diff['opcode'] == 'replace' and diff['type'] == 'otro':
                current_summary_counts['reemplazos_otro'] += 1
            if diff['opcode'] == 'delete':
                current_summary_counts['lineas_eliminadas'] += 1
            elif diff['opcode'] == 'insert':
                current_summary_counts['lineas_agregadas'] += 1

        total_diffs = len(self.all_detailed_diffs)
        categories = {
            'Modificaciones de fecha': ('reemplazos_fecha', '#FFEBEE'),
            'Modificaciones de espaciado': ('reemplazos_espacios', '#FFFDE7'),
            'Otras modificaciones de contenido': ('reemplazos_otro', '#E3F2FD'),
            'Líneas agregadas': ('lineas_agregadas', '#E8F5E9'),
            'Líneas eliminadas': ('lineas_eliminadas', '#FFEBEE')
        }

        # Frame para el texto con scrollbars
        text_frame = ttk.Frame(summary_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.detailed_display_text = tk.Text(text_frame, wrap=tk.NONE, font=('Consolas', 9), bg='#f8f9fa', borderwidth=0, highlightthickness=0)
        
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.detailed_display_text.yview)
        h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.detailed_display_text.xview)
        self.detailed_display_text.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.detailed_display_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # --- CORRECCIÓN: Definir el tag de resaltado para esta ventana ---
        self.detailed_display_text.tag_configure("diff_word", background="#F44336", foreground="white", font=('Consolas', 9, 'bold'))

        self.detailed_display_text.tag_configure("line_num", foreground="#2196F3", font=('Consolas', 9, 'bold'))
        self.detailed_display_text.tag_configure("header", foreground="#2196F3", font=('Consolas', 9, 'bold'))
        self.detailed_display_text.tag_configure("file1_line", foreground="#D32F2F") # Rojo para contenido de archivo 1
        self.detailed_display_text.tag_configure("file2_line", foreground="#388E3C") # Verde para contenido de archivo 2

        for text_label, (key, bg_color) in categories.items():
            count = current_summary_counts[key]
            btn = ttk.Button(summary_counts_frame, text=f"{text_label}: {count}", bootstyle="outline",
                             command=lambda k=key: self._display_detailed_diffs_in_summary(k, summary_window))
            btn.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Botón para mostrar todas las diferencias
        ttk.Button(summary_counts_frame, text=f"Mostrar Todas: {total_diffs}", bootstyle="outline",
                   command=lambda: self._display_detailed_diffs_in_summary(None, summary_window)).pack(side=tk.RIGHT, padx=5, pady=2)

        # Mostrar todas las diferencias inicialmente
        self._display_detailed_diffs_in_summary(None, summary_window)

        # --- Botón de Regresar ---
        bottom_frame = ttk.Frame(summary_window)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(5, 10), side=tk.BOTTOM)
        back_button = ttk.Button(bottom_frame, text="↩️ Regresar", bootstyle="secondary",
                                 command=lambda: self._on_summary_close(summary_window))
        back_button.pack(side=tk.RIGHT)

        summary_window.protocol("WM_DELETE_WINDOW", lambda: self._on_summary_close(summary_window))

    def _on_summary_close(self, summary_window):
        """Libera el grab y destruye la ventana de resumen."""
        # summary_window.grab_release() # Ya no es necesario
        self.summary_window_instance = None # Limpiar la referencia
        summary_window.destroy()
        # --- CORRECCIÓN: Traer la ventana del comparador al frente ---
        self.deiconify()
        self.lift()
        self.focus_force()

    def _display_detailed_diffs_in_summary(self, diff_type_filter, parent_window):
        """
        Muestra las diferencias detalladas en el widget ScrolledText de la ventana de resumen,
        filtrando por tipo si se especifica.
        """
        self.detailed_display_text.config(state=tk.NORMAL)
        self.detailed_display_text.delete(1.0, tk.END)

        if diff_type_filter:
            display_title = f"--- Detalles para: {diff_type_filter.replace('reemplazos_', '').replace('_', ' ').title()} ---\n\n"
        else:
            display_title = "--- Detalles de Todas las Diferencias ---\n\n"
        self.detailed_display_text.insert(tk.END, display_title, "header")

        # --- SOLUCIÓN: Calcular y alinear las etiquetas ANTES del bucle ---
        file1_name = os.path.basename(self.comparison_results[0]['file1'])
        file2_name = os.path.basename(self.comparison_results[0]['file2'])
        
        label1_text = f"ARCHIVO1 ({file1_name}): "
        label2_text = f"ARCHIVO2 ({file2_name}): "
        max_len = max(len(label1_text), len(label2_text))
        
        aligned_label1 = label1_text.ljust(max_len)
        aligned_label2 = label2_text.ljust(max_len)

        for diff_entry in self.all_detailed_diffs:
            # Filtrar por el tipo de diferencia
            match = False
            if diff_type_filter is None: # Mostrar todas
                match = True
            elif diff_entry['opcode'] == 'replace' and f"reemplazos_{diff_entry['type']}" == diff_type_filter:
                match = True
            elif diff_entry['opcode'] == 'delete' and diff_type_filter == 'lineas_eliminadas':
                match = True
            elif diff_entry['opcode'] == 'insert' and diff_type_filter == 'lineas_agregadas':
                match = True
            
            if match:
                self.detailed_display_text.insert(tk.END, f"Línea Archivo1: {diff_entry['file1_line_num']} | Línea Archivo2: {diff_entry['file2_line_num']}\n", "line_num")
                
                # Display File 1 content
                # --- SOLUCIÓN: Usar la etiqueta alineada ---
                self.detailed_display_text.insert(tk.END, aligned_label1, "file1_line")
                start_idx_file1 = self.detailed_display_text.index(tk.END + "-1c")
                self.detailed_display_text.insert(tk.END, f"{diff_entry['file1_content']}\n")
                if diff_entry['opcode'] == 'replace':
                    for char_diff in diff_entry['char_diff_info']:
                        if char_diff['tag'] != 'equal':
                            self.detailed_display_text.tag_add("diff_word",
                                                               f"{start_idx_file1}+{char_diff['file1_char_start']}c",
                                                               f"{start_idx_file1}+{char_diff['file1_char_end']}c")
                elif diff_entry['opcode'] == 'delete':
                    self.detailed_display_text.tag_add("diff_word", start_idx_file1, tk.END + "-1c")

                # Display File 2 content
                # --- SOLUCIÓN: Usar la etiqueta alineada ---
                self.detailed_display_text.insert(tk.END, aligned_label2, "file2_line")
                start_idx_file2 = self.detailed_display_text.index(tk.END + "-1c")
                self.detailed_display_text.insert(tk.END, f"{diff_entry['file2_content']}\n")
                if diff_entry['opcode'] == 'replace':
                    for char_diff in diff_entry['char_diff_info']:
                        if char_diff['tag'] != 'equal':
                            self.detailed_display_text.tag_add("diff_word",
                                                               f"{start_idx_file2}+{char_diff['file2_char_start']}c",
                                                               f"{start_idx_file2}+{char_diff['file2_char_end']}c")
                elif diff_entry['opcode'] == 'insert':
                    self.detailed_display_text.tag_add("diff_word", start_idx_file2, tk.END + "-1c")

                self.detailed_display_text.insert(tk.END, "----------------------------------------\n\n")

        self.detailed_display_text.config(state=tk.DISABLED)

    def _update_compare_button_state(self):
        """Actualiza el estado del botón 'COMPARAR' basado en el número de archivos seleccionados."""
        if len(self.selected_files) >= 2:
            self.compare_button.config(state='normal')
        else:
            self.compare_button.config(state='disabled')
        self.summary_button.pack_forget() # Asegurarse de que el botón de resumen esté oculto

def main():
    """Función principal"""
    # Esta función ya no es necesaria, ya que el comparador se abre desde usu_basico_main.py
    pass

if __name__ == "__main__":
    main()