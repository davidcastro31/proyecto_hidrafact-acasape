import crud_hidrofact
from decimal import Decimal
from datetime import date

db = crud_hidrofact.crud()

class crud_pago:
    def registrar_pago(self, datos):
        """
        Registra un pago y actualiza el estado de las facturas pagadas
        datos: {
            'idUsuario': int,
            'facturas': [id1, id2, ...],
            'montoTotal': float,
            'metodoPago': str
        }
        """
        try:
            fecha_pago = date.today()
            
            # Registrar el pago en la tabla pagos (uno por cada factura)
            facturas_pagadas = []
            
            for idFactura in datos['facturas']:
                # Obtener el monto de la factura
                sql_factura = f"SELECT montoTotal, estado FROM facturas WHERE idFactura = {idFactura}"
                resultado = db.consultar(sql_factura)
                
                if len(resultado) > 0:
                    # Verificar que la factura no esté ya pagada
                    if resultado[0]['estado'] == 'Pagada':
                        continue  # Saltar facturas ya pagadas
                    
                    monto_factura = float(resultado[0]['montoTotal'])
                    
                    # Insertar el pago
                    sql_pago = """
                        INSERT INTO pagos (idFactura, fechaPago, montoPagado, metodoPago)
                        VALUES (%s, %s, %s, %s)
                    """
                    valores_pago = (idFactura, fecha_pago, monto_factura, datos['metodoPago'])
                    resultado_pago = db.ejecutar(sql_pago, valores_pago)
                    
                    if resultado_pago == "ok":
                        # Actualizar el estado de la factura a 'Pagada'
                        sql_update = """
                            UPDATE facturas 
                            SET estado = 'Pagada'
                            WHERE idFactura = %s
                        """
                        db.ejecutar(sql_update, (idFactura,))
                        
                        facturas_pagadas.append(idFactura)
            
            if len(facturas_pagadas) > 0:
                # Obtener el último ID de pago insertado
                sql_ultimo = "SELECT MAX(idPago) as ultimo FROM pagos"
                resultado_ultimo = db.consultar(sql_ultimo)
                ultimo_id = resultado_ultimo[0]['ultimo'] if len(resultado_ultimo) > 0 else 0
                
                return {
                    "status": "ok",
                    "idPago": ultimo_id,
                    "facturasPagadas": facturas_pagadas,
                    "mensaje": f"Se registraron {len(facturas_pagadas)} pago(s) exitosamente"
                }
            else:
                return {
                    "status": "error",
                    "mensaje": "No se pudo registrar ningún pago o las facturas ya están pagadas"
                }
                
        except Exception as e:
            print(f"Error al registrar pago: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "mensaje": str(e)
            }
    
    def consultar_pagos_usuario(self, idUsuario):
        """Obtiene todos los pagos realizados por un usuario"""
        sql = f"""
            SELECT p.*, f.idFactura, f.tipoFactura, f.montoTotal as montoFactura
            FROM pagos p
            INNER JOIN facturas f ON p.idFactura = f.idFactura
            WHERE f.idUsuario = {idUsuario}
            ORDER BY p.fechaPago DESC
        """
        resultado = db.consultar(sql)
        
        # Convertir fechas y decimales
        pagos = []
        for pago in resultado:
            pago_dict = {}
            for key, value in pago.items():
                if isinstance(value, date):
                    pago_dict[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, Decimal):
                    pago_dict[key] = float(value)
                else:
                    pago_dict[key] = value
            pagos.append(pago_dict)
        
        return pagos
    
    def consultar_todos_pagos(self):
        """Obtiene todos los pagos del sistema"""
        sql = """
            SELECT p.*, f.idFactura, f.tipoFactura, f.idUsuario, u.nombre, u.num_contador
            FROM pagos p
            INNER JOIN facturas f ON p.idFactura = f.idFactura
            INNER JOIN usuarios u ON f.idUsuario = u.idUsuario
            ORDER BY p.fechaPago DESC
        """
        resultado = db.consultar(sql)
        
        pagos = []
        for pago in resultado:
            pago_dict = {}
            for key, value in pago.items():
                if isinstance(value, date):
                    pago_dict[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, Decimal):
                    pago_dict[key] = float(value)
                else:
                    pago_dict[key] = value
            pagos.append(pago_dict)
        
        return pagos