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
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

class ModernFileComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de Archivos - Versión Profesional")
        self.root.geometry("1200x680")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.selected_files = []
        self.processed_file_contents = {} # Almacenar contenido procesado para el reporte
        self.comparison_results = []
        
        # Configurar estilo moderno
        self.setup_styles()
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
    
    def setup_styles(self):
        """Configurar estilos modernos para la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores modernos
        colors = {
            'primary': '#2196F3',
            'secondary': '#FFC107',
            'success': '#4CAF50',
            'danger': '#F44336',
            'dark': '#212121',
            'light': '#FAFAFA'
        }
        
        # Configurar estilos personalizados
        style.configure('Modern.TButton',
                       background=colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.map('Modern.TButton',
                 background=[('active', '#1976D2')])
        
        style.configure('Success.TButton',
                       background=colors['success'],
                       foreground='white',
                       borderwidth=2,
                       focuscolor='none',
                       padding=(20, 15),
                       font=('Segoe UI', 11, 'bold'))
        
        style.map('Success.TButton',
                 background=[('active', '#45a049')],
                 relief=[('pressed', 'flat'), ('!pressed', 'raised')])
        
        style.configure('Modern.TFrame',
                       background='#ffffff',
                       relief='flat',
                       borderwidth=1)
    
    def create_interface(self):
        """Crear la interfaz gráfica principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="🔍 Comparador de Archivos Profesional",
                              font=('Segoe UI', 24, 'bold'),
                              bg='#ffffff',
                              fg='#2196F3')
        title_label.pack(pady=(0, 30))
        
        # Contenedor principal para los paneles (ahora estáticos)
        panels_container = ttk.Frame(main_frame, style='Modern.TFrame')
        panels_container.pack(fill=tk.BOTH, expand=True)

        # --- Panel Izquierdo (Controles) ---
        controls_frame = ttk.Frame(panels_container, style='Modern.TFrame', width=350)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y) # Ancho fijo para el panel de controles

        # Frame superior para el resto de los controles
        top_controls_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        top_controls_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.create_file_selection_frame(top_controls_frame)
        self.create_options_frame(top_controls_frame)
        self.create_compare_button_frame(top_controls_frame) # Este botón debe estar en top_controls_frame

        # Frame para los botones de acción inferiores, anclado abajo
        bottom_actions_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        bottom_actions_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        self.create_report_action_buttons(bottom_actions_frame)
        controls_frame.pack_propagate(False) # Evita que el frame se encoja

        # --- Panel Derecho (Resultados) ---
        results_container = ttk.Frame(panels_container, style='Modern.TFrame')
        self.create_results_frame(results_container)
        results_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Ocupa el espacio restante
    
    def create_file_selection_frame(self, parent):
        """Crear frame para selección de archivos"""
        file_frame = ttk.LabelFrame(parent, text="📁 Selección de Archivos", 
                                   style='Modern.TFrame', padding=20)
        file_frame.pack(fill=tk.X, expand=False, pady=(0, 20), padx=10)
        
        # Lista de archivos seleccionados
        self.files_listbox = tk.Listbox(file_frame, 
                                       height=8, # Más altura para ver más archivos
                                       font=('Consolas', 10),
                                       bg='#f8f9fa',
                                       selectbackground='#2196F3',
                                       selectforeground='white', relief=tk.FLAT)
        self.files_listbox.pack(fill=tk.X, pady=(0, 15))
        
        # Configurar drag & drop si está disponible
        if DND_AVAILABLE:
            self.files_listbox.drop_target_register(DND_FILES)
            self.files_listbox.dnd_bind('<<Drop>>', self.on_drop_files)
            drop_text = "💡 Arrastra archivos aquí desde el explorador"
        else:
            drop_text = "💡 (Instala 'tkinterdnd2' para Drag & Drop)"
        
        tk.Label(file_frame, text=drop_text,
                 font=('Segoe UI', 9, 'italic'),
                 bg='#ffffff', fg='#666666').pack(pady=(0, 10))
        
        
        # Botones de gestión de archivos
        buttons_frame = tk.Frame(file_frame, bg='#ffffff')
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="➕ Agregar Archivos", 
                  style='Modern.TButton',
                  command=self.add_files).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        ttk.Button(buttons_frame, text="🗑️ Eliminar Seleccionado", 
                  command=self.remove_selected_file).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        ttk.Button(buttons_frame, text="🧹 Limpiar Todo", 
                  command=self.clear_all_files).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    def create_options_frame(self, parent):
        """Crear frame de opciones de comparación"""
        options_frame = ttk.LabelFrame(parent, text="⚙️ Opciones de Comparación", 
                                      style='Modern.TFrame', padding=20)
        options_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        # Variables de opciones
        self.ignore_whitespace = tk.BooleanVar(value=False)
        self.ignore_case = tk.BooleanVar(value=False)
        self.show_context = tk.BooleanVar(value=True)
        self.sync_scroll = tk.BooleanVar(value=True)
        
        # Checkboxes
        tk.Checkbutton(options_frame, text="Ignorar espacios en blanco",
                      variable=self.ignore_whitespace,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        tk.Checkbutton(options_frame, text="Ignorar mayúsculas/minúsculas",
                      variable=self.ignore_case,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        tk.Checkbutton(options_frame, text="Mostrar contexto en diferencias",
                      variable=self.show_context,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        tk.Checkbutton(options_frame, text="Sincronizar scroll vertical",
                      variable=self.sync_scroll,
                      bg='#ffffff', font=('Segoe UI', 10)).pack(anchor=tk.W)
    
    def create_results_frame(self, parent):
        """Crear frame para mostrar resultados"""
        results_frame = ttk.LabelFrame(parent, text="📊 Resultados de Comparación", 
                                      style='Modern.TFrame', padding=20)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # RF10.1: Contenedor tipo splitter horizontal
        panels_display_frame = ttk.Frame(results_frame, style='Modern.TFrame')
        panels_display_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid para que las dos columnas tengan el mismo peso
        panels_display_frame.grid_columnconfigure(0, weight=1)
        panels_display_frame.grid_columnconfigure(1, weight=1)
        panels_display_frame.grid_rowconfigure(0, weight=1) # Solo una fila

        # Panel A (Izquierda)
        frame_a = ttk.Frame(panels_display_frame, style='Modern.TFrame')
        self.text_a, self.cursor_pos_label_a = self._create_text_widget(frame_a, is_left_panel=True)
        frame_a.grid(row=0, column=0, sticky="nsew") # Empaquetar con grid

        # Panel B (Derecha)
        frame_b = ttk.Frame(panels_display_frame, style='Modern.TFrame')
        self.text_b, self.cursor_pos_label_b = self._create_text_widget(frame_b, is_left_panel=False)
        frame_b.grid(row=0, column=1, sticky="nsew") # Empaquetar con grid

        # Actualizar posición inicial del cursor
        self._update_cursor_position_display(self.text_a, self.cursor_pos_label_a)
        self._update_cursor_position_display(self.text_b, self.cursor_pos_label_b)

        # Sincronizar scroll
        # La configuración se hace en _create_text_widget para tener acceso a las scrollbars

        # Configurar tags para colores
        for text_widget in [self.text_a, self.text_b]:
            text_widget.tag_configure("diff", background="#FFEBEE") # Rojo claro para diferencias
            text_widget.tag_configure("diff_word", background="#F44336", foreground="white", font=('Consolas', 10, 'bold')) # Rojo intenso
            text_widget.tag_configure("header", foreground="#2196F3", font=('Consolas', 10, 'bold'))

    def _create_text_widget(self, parent, is_left_panel=True):
        """Crea un widget de texto con scrollbars e indicador de posición del cursor."""
        container_frame = tk.Frame(parent, bg='#f8f9fa')
        container_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configurar grid para container_frame: una columna para text_frame (expansible), otra para diff_map (ancho fijo)
        container_frame.grid_columnconfigure(0, weight=1) # Columna para text_frame
        container_frame.grid_columnconfigure(1, weight=0) # Columna para diff_map (ancho fijo)
        container_frame.grid_rowconfigure(0, weight=1) # Solo una fila para el contenido principal

        # Frame para el texto y sus scrollbars
        text_frame = tk.Frame(container_frame, bg='#f8f9fa', relief=tk.GROOVE, borderwidth=1)
        text_frame.grid(row=0, column=0, sticky="nsew") # Colocar text_frame en la primera columna
        text = tk.Text(text_frame, wrap=tk.NONE, font=('Consolas', 10), 
                       bg='#f8f9fa', borderwidth=0, highlightthickness=0)
        
        # Asignar el comando de scroll correcto para la sincronización
        # La sincronización se maneja a través de los comandos de las scrollbars
        scroll_command = self._on_scroll_a_y if is_left_panel else self._on_scroll_b_y
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=scroll_command)
        h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text.xview)
        text.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Indicador de posición de línea y carácter
        cursor_pos_label = tk.Label(text_frame, text="L: 1, C: 0", font=('Consolas', 9), bg='#f8f9fa', anchor=tk.W)
        cursor_pos_label.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)

        # Bind events to update cursor position display
        text.bind("<KeyRelease>", lambda event: self._update_cursor_position_display(text, cursor_pos_label))
        text.bind("<ButtonRelease-1>", lambda event: self._update_cursor_position_display(text, cursor_pos_label))
        text.bind("<Motion>", lambda event: self._update_cursor_position_display(text, cursor_pos_label), add='+')

        # Barra de marcadores de diferencias (Diff Map)
        diff_map = tk.Canvas(container_frame, width=15, bg='#e0e0e0', highlightthickness=0)
        diff_map.grid(row=0, column=1, sticky="nsew", padx=(2, 0)) # Colocar diff_map en la segunda columna
        diff_map.bind("<Button-1>", lambda event: self._on_marker_click(event, diff_map))

        # Asignar a atributos de la clase
        if is_left_panel:
            self.diff_map_a = diff_map
        else:
            self.diff_map_b = diff_map

        
        return text, cursor_pos_label

    def _update_cursor_position_display(self, text_widget, label_widget):
        """Actualiza la etiqueta con la posición actual del cursor (línea y carácter)."""
        try:
            cursor_index = text_widget.index(tk.INSERT)
            line, char = map(int, cursor_index.split('.'))
            label_widget.config(text=f"L: {line}, C: {char}")
        except tk.TclError:
            # Esto puede ocurrir si el widget no está completamente inicializado o está vacío.
            label_widget.config(text="L: ?, C: ?")

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

    def _on_scroll_b_y(self, *args):
        """Maneja el scroll vertical del panel B y sincroniza con A."""
        if self.sync_scroll.get():
            self.text_b.yview(*args) # Mueve el panel B.
            self.text_a.yview(*args) # Sincroniza el panel A con la misma acción.
        else:
            self.text_b.yview(*args)

    def create_compare_button_frame(self, parent):
        """Crea un frame dedicado para el botón COMPARAR"""
        compare_frame = tk.Frame(parent, bg='#ffffff')
        compare_frame.pack(fill=tk.X, pady=(10, 20), padx=10) # Padding para separarlo
        
        self.compare_button = ttk.Button(compare_frame, text="🔍 COMPARAR", 
                  style='Success.TButton',
                  command=self.compare_files,
                  state='disabled') # Deshabilitado inicialmente
        self.compare_button.pack(side=tk.TOP, expand=True, fill=tk.X) # Ocupa todo el ancho

    def create_report_action_buttons(self, parent):
        """Crear botones de acción de reporte (Guardar y Limpiar Resultados)"""
        report_action_frame = tk.Frame(parent, bg='#ffffff')
        report_action_frame.pack(fill=tk.X, padx=10, pady=10) # Padding consistente
        
        ttk.Button(report_action_frame, text="💾 Guardar Reporte", 
                  style='Modern.TButton',
                  command=self.save_report).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        ttk.Button(report_action_frame, text="🧹 Limpiar Resultados", 
                  command=self.clear_results).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    def center_window(self):
        """Centrar la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2) - 40 # Subir la ventana 50px
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
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
            files = self.root.tk.splitlist(event.data)
        else:
            return
        
        added_count = 0
        for file_path in files:
            if os.path.isfile(file_path) and file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.files_listbox.insert(tk.END, os.path.basename(file_path))
                added_count += 1
        
        if added_count > 0:
            messagebox.showinfo("Archivos agregados", 
                              f"Se agregaron {added_count} archivo(s) por drag & drop")
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
        self._update_compare_button_state()
    
    def clear_results(self):
        """Limpiar resultados"""
        self.comparison_results.clear()
        for widget in [self.text_a, self.text_b]:
            widget.config(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.config(state=tk.DISABLED)
        # Limpiar indicadores de cursor
        self.cursor_pos_label_a.config(text="L: 1, C: 0")
        self.cursor_pos_label_b.config(text="L: 1, C: 0")
    
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
        self.root.update()
        
        # Ejecutar comparación en hilo separado
        thread = threading.Thread(target=self._perform_comparison)
        thread.daemon = True
        thread.start()
    
    def _perform_comparison(self):
        """Realizar la comparación de archivos"""
        # RF2: Crear la carpeta C:\comparador si no existe
        output_dir = Path("C:/comparador")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.comparison_results.clear()
            self.processed_file_contents.clear()
            
            # Leer y pre-procesar contenido de archivos
            file_contents = {}
            for file_path in self.selected_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if self.ignore_case.get():
                            content = content.lower()
                        if self.ignore_whitespace.get():
                            content = '\n'.join(line.strip() for line in content.splitlines())
                        file_contents[file_path] = content.splitlines()
                        self.processed_file_contents[file_path] = content.splitlines() # Store processed content
                except Exception as e:
                    error_msg = f"❌ Error leyendo {os.path.basename(file_path)}: {str(e)}\n"
                    self.root.after(0, lambda msg=error_msg: self.text_a.insert(tk.END, msg))

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
            self.root.after(0, self._finalize_comparison)
            
        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", f"Error durante la comparación: {str(err)}"))
    
    def _compare_pair(self, file1_path, file2_path, content1_processed, content2_processed):
        """Comparar un par de archivos"""
        name1 = os.path.basename(file1_path)
        name2 = os.path.basename(file2_path)
        
        # Usar SequenceMatcher para obtener opcodes, que es más útil para la vista de dos paneles
        matcher = difflib.SequenceMatcher(None, content1_processed, content2_processed)
        
        # Almacenar resultados
        comparison_result = {
            'file1': file1_path,
            'file2': file2_path,
            'opcodes': matcher.get_opcodes(),
            'has_differences': matcher.ratio() < 1.0
        }
        self.comparison_results.append(comparison_result)
        
        # Mostrar resultados en la interfaz
        # La visualización se hará una vez para el primer par comparado
        if len(self.comparison_results) == 1:
            self.root.after(0, lambda: self._display_comparison(comparison_result))
    
    def _display_comparison(self, result):
        """Mostrar comparación en la interfaz"""
        # La visualización se hará una vez para el primer par comparado
        if len(self.comparison_results) == 1:
            first_result = self.comparison_results[0]
            content1 = self.processed_file_contents.get(first_result['file1'], [])
            content2 = self.processed_file_contents.get(first_result['file2'], [])
            opcodes = first_result['opcodes']

            # Limpiar y habilitar paneles
            for widget in [self.text_a, self.text_b]:
                widget.config(state=tk.NORMAL)
                widget.delete(1.0, tk.END)

            # Poblar paneles y resaltar diferencias
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    for i in range(i1, i2):
                        self.text_a.insert(tk.END, content1[i] + '\n')
                    for j in range(j1, j2):
                        self.text_b.insert(tk.END, content2[j] + '\n')
                
                elif tag == 'replace':
                    # Diferencia a nivel de palabra para reemplazos
                    num_lines = max(i2 - i1, j2 - j1)
                    for i in range(num_lines):
                        line1 = content1[i1 + i] if i1 + i < i2 else ""
                        line2 = content2[j1 + i] if j1 + i < j2 else ""
                        self._highlight_char_diffs(line1, line2)
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
            for widget in [self.text_a, self.text_b]:
                widget.config(state=tk.DISABLED)
            
            # Asegurar que ambos paneles comiencen desde la parte superior
            self.text_a.yview_moveto(0.0)
            self.text_b.yview_moveto(0.0)

    def _highlight_char_diffs(self, line1, line2):
        """
        Compara dos líneas carácter por carácter y resalta las diferencias exactas.
        """
        # 1. Insertar las líneas y aplicar el resaltado de fondo claro a toda la línea
        self.text_a.insert(tk.END, line1 + '\n', 'diff')
        self.text_b.insert(tk.END, line2 + '\n', 'diff')

        # 2. Obtener la posición de la línea recién insertada (es la penúltima)
        # El índice es "line.char", así que extraemos solo la parte de la línea.
        line_num_a = self.text_a.index('end-2l').split('.')[0]
        line_num_b = self.text_b.index('end-2l').split('.')[0]

        # 3. Usar SequenceMatcher a nivel de carácter
        matcher = difflib.SequenceMatcher(None, line1, line2)

        # 4. Aplicar el resaltado intenso a las secciones diferentes
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                # Construir el índice correctamente en formato "linea.columna"

                # Resaltar en el panel A
                start_a = f"{line_num_a}.{i1}"
                end_a = f"{line_num_a}.{i2}"
                self.text_a.tag_add("diff_word", start_a, end_a)
                
                # Resaltar en el panel B
                start_b = f"{line_num_b}.{j1}"
                end_b = f"{line_num_b}.{j2}"
                self.text_b.tag_add("diff_word", start_b, end_b)

    def _finalize_comparison(self):
        """Mostrar resumen final y generar reporte."""
        total_comparisons = len(self.comparison_results)
        files_with_differences = sum(1 for r in self.comparison_results if r['has_differences'])
        
        summary = f"\n{'='*80}\n📊 RESUMEN DE COMPARACIÓN\n{'='*80}\n"
        summary += f"Total de comparaciones realizadas: {total_comparisons}\n"
        summary += f"Pares con diferencias: {files_with_differences}\n"
        summary += f"Pares idénticos: {total_comparisons - files_with_differences}\n"
        summary += f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Mostrar resumen en la parte inferior del primer panel
        self.text_a.config(state=tk.NORMAL)
        self.text_a.insert(tk.END, "\n\n" + summary, "header")
        self.text_a.config(state=tk.DISABLED)
        # Posicionar ambos paneles al inicio después de agregar el resumen
        self.text_a.yview_moveto(0.0)
        self.text_b.yview_moveto(0.0)

        self.compare_button.config(state='normal') # Habilitar de nuevo

        # Generar reporte automáticamente al finalizar
        if self.comparison_results:
            self.save_report()
    
    def save_report(self):
        """Guardar reporte de diferencias"""
        if not self.comparison_results:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar")
            return
        
        if len(self.selected_files) < 2:
            messagebox.showwarning("Advertencia", "Se requieren al menos dos archivos para generar un reporte detallado.")
            return
        
        # RF2: Asegurar que la carpeta C:\comparador existe
        output_dir = Path("C:/comparador")
        output_dir.mkdir(parents=True, exist_ok=True) # Asegura que la carpeta existe
        
        # RF3: Nombre del archivo determinístico
        if not self.selected_files:
            messagebox.showerror("Error", "No hay archivos seleccionados para determinar el nombre del reporte.")
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
                    
                    total_lines_file1 = len(content1_processed)
                    total_lines_file2 = len(content2_processed)
                    
                    matcher = difflib.SequenceMatcher(None, content1_processed, content2_processed)
                    diff_count = 0
                    for opcode, _, _, _, _ in matcher.get_opcodes():
                        if opcode != 'equal':
                            diff_count += 1
                    
                    f.write(f"Total líneas Archivo1: {total_lines_file1}\n")
                    f.write(f"Total líneas Archivo2: {total_lines_file2}\n")
                    f.write(f"DIFERENCIAS: {diff_count}\n")
                    f.write("Notas: Diferencias encontradas en el contenido de los archivos.\n")
                    f.write("\n")
                    
                    # RF4, RF5: DATOS TOTALES
                    f.write("DATOS TOTALES\n")
                    f.write(f"Líneas Archivo1: {total_lines_file1}\n")
                    f.write(f"Líneas Archivo2: {total_lines_file2}\n")
                    
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
                    
                    if diff_count == 0:
                        f.write("No se encontraron diferencias.\n")
                    else:
                        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
                            if opcode == 'replace':
                                f.write(f"\n--- Diferencia en línea(s) {i1 + 1}-{i2} (Archivo1) y {j1 + 1}-{j2} (Archivo2) ---\n")
                                for line_num in range(i1, i2):
                                    f.write(f"LÍNEA {line_num + 1}\n")
                                    f.write(f"ARCHIVO1: \"{content1_processed[line_num]}\"\n")
                                    f.write(f"ARCHIVO2: \"{content2_processed[j1 + (line_num - i1)] if j1 + (line_num - i1) < j2 else ''}\"\n")
                                    f.write("DIFERENCIA: Contenido distinto\n")
                            elif opcode == 'delete':
                                f.write(f"\n--- Línea(s) {i1 + 1}-{i2} eliminada(s) de Archivo1 ---\n")
                                for line_num in range(i1, i2):
                                    f.write(f"LÍNEA {line_num + 1}\n")
                                    f.write(f"ARCHIVO1: \"{content1_processed[line_num]}\"\n")
                                    f.write("ARCHIVO2: \"\"\n")
                                    f.write("DIFERENCIA: Línea eliminada\n")
                            elif opcode == 'insert':
                                f.write(f"\n--- Línea(s) {j1 + 1}-{j2} agregada(s) en Archivo2 ---\n")
                                for line_num in range(j1, j2):
                                    f.write(f"LÍNEA {line_num + 1} (en Archivo2)\n")
                                    f.write("ARCHIVO1: \"\"\n")
                                    f.write(f"ARCHIVO2: \"{content2_processed[line_num]}\"\n")
                                    f.write("DIFERENCIA: Línea agregada\n")
                else:
                    f.write("No se pudieron obtener los contenidos de los archivos para el reporte detallado.\n")
                
                f.write("\nFIN DEL INFORME\n")
            
            messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en:\n{report_filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el reporte: {str(e)}")
    
    def _update_compare_button_state(self):
        """Actualiza el estado del botón 'COMPARAR' basado en el número de archivos seleccionados."""
        if len(self.selected_files) >= 2:
            self.compare_button.config(state='normal')
        else:
            self.compare_button.config(state='disabled')

def main():
    """Función principal"""
    # Usar TkinterDnD.Tk() si DND está disponible
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ModernFileComparator(root)
    root.mainloop()

if __name__ == "__main__":
    main()