# Mock del módulo styles para evitar errores de importación en tests
# Este archivo permite que los tests funcionen sin dependencias externas

def mock_function(*args, **kwargs):
    """Función mock genérica"""
    pass

# Funciones mock para todas las importaciones de styles
etiqueta_titulo = mock_function
entrada_estandar = mock_function
boton_accion = mock_function
boton_exito = mock_function
boton_rojo = mock_function
boton_comun = mock_function
img_boton = mock_function

# Exportar todas las funciones que pueden ser importadas
__all__ = [
    'etiqueta_titulo',
    'entrada_estandar', 
    'boton_accion',
    'boton_exito',
    'boton_rojo',
    'boton_comun',
    'img_boton'
]