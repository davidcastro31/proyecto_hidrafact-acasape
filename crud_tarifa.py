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
    
    def modificar(self, datos):
        """Modifica el precio de una tarifa"""
        sql = """
            UPDATE tarifas 
            SET precioUnitario=%s
            WHERE idTarifa=%s
        """
        valores = (
            datos['precioUnitario'],
            datos['idTarifa']
        )
        
        return db.ejecutar(sql, valores)