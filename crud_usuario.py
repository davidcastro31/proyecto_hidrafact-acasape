import crud_hidrofact

db = crud_hidrofact.crud()

class crud_usuario:
    def consultar(self, buscar=""):
        """Consulta usuarios, permite búsqueda por nombre o número de contador"""
        if buscar:
            sql = f"""
                SELECT * FROM usuarios 
                WHERE nombre LIKE '%{buscar}%' 
                OR num_contador LIKE '%{buscar}%'
                ORDER BY nombre
            """
        else:
            sql = "SELECT * FROM usuarios ORDER BY nombre"
        
        return db.consultar(sql)
    
    def administrar(self, datos):
        """Maneja agregar, modificar y eliminar usuarios"""
        if datos['accion'] == "nuevo":
            sql = """
                INSERT INTO usuarios (num_contador, nombre, correo, estado)
                VALUES (%s, %s, %s, %s)
            """
            valores = (
                datos['num_contador'],
                datos['nombre'],
                datos['correo'],
                datos['estado']
            )
        
        elif datos['accion'] == "modificar":
            sql = """
                UPDATE usuarios 
                SET num_contador=%s, nombre=%s, correo=%s, estado=%s
                WHERE idUsuario=%s
            """
            valores = (
                datos['num_contador'],
                datos['nombre'],
                datos['correo'],
                datos['estado'],
                datos['idUsuario']
            )
        
        elif datos['accion'] == "eliminar":
            sql = "DELETE FROM usuarios WHERE idUsuario=%s"
            valores = (datos['idUsuario'],)
        
        return db.ejecutar(sql, valores)