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
        
        elif datos['accion'] == "modificar":
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
        
        elif datos['accion'] == "eliminar":
            sql = "DELETE FROM lecturas WHERE idLectura=%s"
            valores = (datos['idLectura'],)
        
        return db.ejecutar(sql, valores)