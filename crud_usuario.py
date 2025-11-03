import crud_hidrofact

db = crud_hidrofact.crud()

class crud_usuario:
    def actualizar_estados_facturas(self):
        """Actualiza el estado de facturas vencidas antes de consultar"""
        try:
            sql_update = """
                UPDATE facturas 
                SET estado = 'Vencida'
                WHERE estado = 'Pendiente' 
                AND fechaVencimiento < CURDATE()
            """
            db.ejecutar(sql_update, ())
        except Exception as e:
            print(f"Error al actualizar estados: {e}")
    
    def consultar(self, buscar=""):
        """Consulta usuarios con conteo de facturas vencidas"""
        # Primero actualizar estados de facturas
        self.actualizar_estados_facturas()
        
        if buscar:
            sql = f"""
                SELECT u.*, 
                    (SELECT COUNT(*) FROM facturas f 
                     WHERE f.idUsuario = u.idUsuario 
                     AND f.estado = 'Vencida') as facturas_vencidas
                FROM usuarios u
                WHERE u.nombre LIKE '%{buscar}%' 
                OR u.num_contador LIKE '%{buscar}%'
                ORDER BY u.idUsuario
            """
        else:
            sql = """
                SELECT u.*, 
                    (SELECT COUNT(*) FROM facturas f 
                     WHERE f.idUsuario = u.idUsuario 
                     AND f.estado = 'Vencida') as facturas_vencidas
                FROM usuarios u
                ORDER BY u.idUsuario
            """
        
        return db.consultar(sql)
    
    def verificar_contador_existente(self, num_contador, idUsuario=None):
        """Verifica si un número de contador ya existe"""
        if idUsuario:
            # Al modificar, excluir el usuario actual
            sql = f"SELECT * FROM usuarios WHERE num_contador='{num_contador}' AND idUsuario != {idUsuario}"
        else:
            # Al agregar nuevo
            sql = f"SELECT * FROM usuarios WHERE num_contador='{num_contador}'"
        
        resultado = db.consultar(sql)
        return len(resultado) > 0
    
    def administrar(self, datos):
        """Maneja agregar, modificar y eliminar usuarios"""
        if datos['accion'] == "nuevo":
            # Verificar si el contador ya existe
            if self.verificar_contador_existente(datos['num_contador']):
                return "El número de contador ya está registrado para otro usuario"
            
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
            # Verificar si el contador ya existe en otro usuario
            if self.verificar_contador_existente(datos['num_contador'], datos['idUsuario']):
                return "El número de contador ya está registrado para otro usuario"
            
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