import logging
import traceback

# Configuración básica de logging
logging.basicConfig(
    filename='app.log',  # Nombre del archivo donde se guardarán los logs
    level=logging.ERROR,  # Nivel mínimo de severidad para registrar mensajes
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato de los mensajes de log
)

def log(mensaje):
    """Función para registrar mensajes en el log."""
    logging.info(mensaje)
    print(mensaje)  # También imprimimos el mensaje en consola

def iniciar_aplicacion():
    """Función principal de la aplicación."""
    # Aquí va el código principal de la aplicación
    log("🔄 Iniciando la aplicación...")
    # Simulamos un error para demostrar el manejo de excepciones
    # raise ValueError("Este es un error de ejemplo.")

def main():
    try:
        # Código principal de la aplicación
        log("🔄 Iniciando la aplicación...")
        iniciar_aplicacion()
    except Exception as e:
        logging.error("❌ Error global inesperado: %s", str(e))
        logging.error(traceback.format_exc())
        print("❌ Error global inesperado. Revisa el log para más detalles.")

if __name__ == "__main__":
    main()