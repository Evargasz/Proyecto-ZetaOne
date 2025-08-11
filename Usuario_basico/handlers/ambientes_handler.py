import json

class ambientesHandler:
    def __init__(self, ruta_json):
        self.ruta_json = ruta_json
        self.ambientes = []
        self.cargar_ambientes()
        

    def cargar_ambientes(self):
        try:
            with open(self.ruta_json, "r", encoding='utf-8') as amb:
                self.ambientes = json.load(amb)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.ambientes = []
            print(f"Error cargando el archivo de ambientes: {e}")

    def listar_ambientes(self):
        #devuelve la lista completa de ambientes

        return self.ambientes
    
    def buscar_ambiente_por_descripcion(self, descripcion):
        #devuelve un ambiente cuyo campo descripcion (o nombre) coincida exactamente

        return next((a for a in self.ambientes if a.get('nombre', '').lower() == descripcion.lower()), None)