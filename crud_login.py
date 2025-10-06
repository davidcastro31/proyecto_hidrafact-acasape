import crud_hidrofact

db = crud_hidrofact.crud()

class crud_login:
    def verificar(self, usuario, clave):
        """Verifica si el usuario y contraseña son correctos"""
        try:
            resultado = db.consultar(
                f"SELECT * FROM login WHERE usuario='{usuario}' AND clave='{clave}'"
            )
            
            if len(resultado) > 0:
                return {
                    "status": "ok",
                    "rol": resultado[0]['rol'],
                    "usuario": resultado[0]['usuario']
                }
            else:
                return {
                    "status": "error",
                    "msg": "Usuario o contraseña incorrectos"
                }
        except Exception as e:
            return {
                "status": "error",
                "msg": f"Error en la base de datos: {str(e)}"
            }