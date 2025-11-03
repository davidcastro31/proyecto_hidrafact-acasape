import crud_hidrofact
from decimal import Decimal
from datetime import date

db = crud_hidrofact.crud()

class crud_lectura:
    def consultar_por_usuario(self, idUsuario):
        """Obtiene todas las lecturas de un usuario específico"""
        sql = f"""
            SELECT * FROM lecturas 
            WHERE idUsuario={idUsuario}
            ORDER BY fechaLectura DESC
        """
        resultado = db.consultar(sql)
        
        # Convertir fechas y decimales a formatos serializables
        lecturas = []
        for lectura in resultado:
            lectura_dict = {}
            for key, value in lectura.items():
                if isinstance(value, date):
                    lectura_dict[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, Decimal):
                    lectura_dict[key] = float(value)
                else:
                    lectura_dict[key] = value
            lecturas.append(lectura_dict)
        
        return lecturas
    
    def obtener_ultima_lectura(self, idUsuario):
        """Obtiene la última lectura de un usuario para usarla como lectura anterior"""
        sql = f"""
            SELECT lecturaActual FROM lecturas 
            WHERE idUsuario={idUsuario}
            ORDER BY fechaLectura DESC
            LIMIT 1
        """
        resultado = db.consultar(sql)
        if len(resultado) > 0:
            valor = resultado[0]['lecturaActual']
            return float(valor) if isinstance(valor, Decimal) else valor
        else:
            return 0
    
    def administrar(self, datos):
        """Maneja agregar, modificar y eliminar lecturas"""
        if datos['accion'] == "nuevo":
            sql = """
                INSERT INTO lecturas (idUsuario, fechaLectura, lecturaAnterior, lecturaActual, consumoM3)
                VALUES (%s, %s, %s, %s, %s)
            """
            valores = (
                datos['idUsuario'],
                datos['fechaLectura'],
                datos['lecturaAnterior'],
                datos['lecturaActual'],
                datos['consumoM3']
            )
            return db.ejecutar(sql, valores)
        
        elif datos['accion'] == "modificar":
            # Verificar si tiene factura asociada (NO SE PUEDE MODIFICAR)
            sql_check = f"SELECT idFactura FROM facturas WHERE idLectura = {datos['idLectura']}"
            resultado_check = db.consultar(sql_check)
            
            if len(resultado_check) > 0:
                return "No se puede modificar una lectura que tiene una factura asociada. Elimine primero la factura."
            
            # Si no tiene factura, permitir modificación
            sql = """
                UPDATE lecturas 
                SET fechaLectura=%s, lecturaAnterior=%s, lecturaActual=%s, consumoM3=%s
                WHERE idLectura=%s
            """
            valores = (
                datos['fechaLectura'],
                datos['lecturaAnterior'],
                datos['lecturaActual'],
                datos['consumoM3'],
                datos['idLectura']
            )
            
            return db.ejecutar(sql, valores)
        
        elif datos['accion'] == "eliminar":
            # Verificar si hay factura asociada (NO SE PUEDE ELIMINAR)
            sql_check = f"SELECT idFactura FROM facturas WHERE idLectura = {datos['idLectura']}"
            resultado_check = db.consultar(sql_check)
            
            if len(resultado_check) > 0:
                return "No se puede eliminar una lectura que tiene una factura asociada. Elimine primero la factura."
            
            sql = "DELETE FROM lecturas WHERE idLectura=%s"
            valores = (datos['idLectura'],)
            return db.ejecutar(sql, valores)
        
        return "Acción no reconocida"