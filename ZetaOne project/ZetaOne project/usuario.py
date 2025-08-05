# usuario.py

class UsuarioSesion:
    usuario = None
    rol = None
    autenticado = False

    @classmethod
    def iniciar(cls, usuario, rol):
        cls.usuario = usuario
        cls.rol = rol
        cls.autenticado = True

    @classmethod
    def cerrar(cls):
        cls.usuario = None
        cls.rol = None
        cls.autenticado = False