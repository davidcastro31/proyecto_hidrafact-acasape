import crud_hidrofact
from decimal import Decimal

db = crud_hidrofact.crud()

class crud_tarifa:
    def consultar(self):
        """Obtiene todas las tarifas"""
        sql = "SELECT * FROM tarifas ORDER BY idTarifa"
        resultado = db.consultar(sql)
        
        # Convertir Decimales a float
        tarifas = []
        for tarifa in resultado:
            tarifa_dict = {}
            for key, value in tarifa.items():
                if isinstance(value, Decimal):
                    tarifa_dict[key] = float(value)
                else:
                    tarifa_dict[key] = value
            tarifas.append(tarifa_dict)
        
        return tarifas
    
    def verificar_concepto_existente(self, concepto, idTarifa=None):
        """Verifica si un concepto ya existe"""
        if idTarifa:
            sql = f"SELECT * FROM tarifas WHERE concepto='{concepto}' AND idTarifa != {idTarifa}"
        else:
            sql = f"SELECT * FROM tarifas WHERE concepto='{concepto}'"
        
        resultado = db.consultar(sql)
        return len(resultado) > 0
    
    def administrar(self, datos):
        """Maneja agregar, modificar y eliminar tarifas"""
        if datos['accion'] == "nueva":
            # Verificar si el concepto ya existe
            if self.verificar_concepto_existente(datos['concepto']):
                return "El concepto de tarifa ya existe"
            
            sql = """
                INSERT INTO tarifas (concepto, precioUnitario)
                VALUES (%s, %s)
            """
            valores = (
                datos['concepto'],
                datos['precioUnitario']
            )
        
        elif datos['accion'] == "modificar":
            sql = """
                UPDATE tarifas 
                SET precioUnitario=%s
                WHERE idTarifa=%s
            """
            valores = (
                datos['precioUnitario'],
                datos['idTarifa']
            )
        
        elif datos['accion'] == "eliminar":
            sql = "DELETE FROM tarifas WHERE idTarifa=%s"
            valores = (datos['idTarifa'],)
        
        return db.ejecutar(sql, valores)