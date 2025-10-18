import crud_hidrofact
from decimal import Decimal
from datetime import date, timedelta

db = crud_hidrofact.crud()

class crud_factura:
    def actualizar_estados_vencidos(self):
        """Actualiza el estado de facturas vencidas y aplica mora"""
        try:
            # Obtener facturas pendientes vencidas
            sql_select = """
                SELECT idFactura, subtotal FROM facturas 
                WHERE estado = 'Pendiente' 
                AND fechaVencimiento < CURDATE()
            """
            facturas_vencidas = db.consultar(sql_select)
            
            if len(facturas_vencidas) == 0:
                return
            
            # Obtener el monto de mora
            tarifas = self.obtener_tarifas()
            mora_monto = tarifas.get('MORA (RECIBO VENCIDO)', 2.00)
            
            # Actualizar cada factura individualmente
            for factura in facturas_vencidas:
                subtotal = float(factura['subtotal']) if isinstance(factura['subtotal'], Decimal) else factura['subtotal']
                nuevo_total = subtotal + mora_monto
                
                sql_update = """
                    UPDATE facturas 
                    SET estado = %s, mora = %s, montoTotal = %s
                    WHERE idFactura = %s
                """
                db.ejecutar(sql_update, ('Vencida', mora_monto, nuevo_total, factura['idFactura']))
                
        except Exception as e:
            print(f"Error al actualizar estados vencidos: {e}")
    
    def actualizar_factura_desde_lectura(self, idLectura, nuevo_consumo):
        """Actualiza una factura cuando se modifica su lectura asociada"""
        try:
            # Buscar la factura asociada a esta lectura
            sql = f"SELECT * FROM facturas WHERE idLectura = {idLectura}"
            resultado = db.consultar(sql)
            
            if len(resultado) == 0:
                return "ok"  # No hay factura asociada, no hay que actualizar nada
            
            factura = resultado[0]
            
            # Verificar si tiene mora (no la perdemos si ya la tiene)
            tiene_mora = float(factura['mora']) > 0 if factura['mora'] else False
            
            # Recalcular monto
            calculo = self.calcular_factura_consumo(nuevo_consumo, tiene_mora)
            
            # Actualizar factura
            sql_update = """
                UPDATE facturas 
                SET subtotal = %s, mora = %s, montoTotal = %s
                WHERE idFactura = %s
            """
            valores = (
                calculo['subtotal'],
                calculo['mora'],
                calculo['total'],
                factura['idFactura']
            )
            
            return db.ejecutar(sql_update, valores)
            
        except Exception as e:
            print(f"Error al actualizar factura desde lectura: {e}")
            return str(e)
    
    def consultar_por_usuario(self, idUsuario):
        """Obtiene todas las facturas de un usuario específico"""
        # Primero actualizar estados vencidos
        self.actualizar_estados_vencidos()
        
        sql = f"""
            SELECT f.*, u.nombre, u.num_contador, u.correo
            FROM facturas f
            INNER JOIN usuarios u ON f.idUsuario = u.idUsuario
            WHERE f.idUsuario = {idUsuario}
            ORDER BY f.fechaEmision DESC
        """
        resultado = db.consultar(sql)
        
        # Convertir fechas y decimales a formatos serializables
        facturas = []
        for factura in resultado:
            factura_dict = {}
            for key, value in factura.items():
                if isinstance(value, date):
                    factura_dict[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, Decimal):
                    factura_dict[key] = float(value)
                else:
                    factura_dict[key] = value
            facturas.append(factura_dict)
        
        return facturas
    
    def consultar_todas(self):
        """Obtiene todas las facturas del sistema"""
        # Primero actualizar estados vencidos
        self.actualizar_estados_vencidos()
        
        sql = """
            SELECT f.*, u.nombre, u.num_contador, u.correo
            FROM facturas f
            INNER JOIN usuarios u ON f.idUsuario = u.idUsuario
            ORDER BY f.fechaEmision DESC
        """
        resultado = db.consultar(sql)
        
        facturas = []
        for factura in resultado:
            factura_dict = {}
            for key, value in factura.items():
                if isinstance(value, date):
                    factura_dict[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, Decimal):
                    factura_dict[key] = float(value)
                else:
                    factura_dict[key] = value
            facturas.append(factura_dict)
        
        return facturas
    
    def verificar_factura_existente(self, idLectura):
        """Verifica si ya existe una factura para una lectura"""
        sql = f"SELECT * FROM facturas WHERE idLectura = {idLectura}"
        resultado = db.consultar(sql)
        return len(resultado) > 0
    
    def obtener_tarifas(self):
        """Obtiene todas las tarifas del sistema"""
        sql = "SELECT * FROM tarifas"
        resultado = db.consultar(sql)
        
        tarifas = {}
        for tarifa in resultado:
            concepto = tarifa['concepto']
            precio = float(tarifa['precioUnitario']) if isinstance(tarifa['precioUnitario'], Decimal) else tarifa['precioUnitario']
            tarifas[concepto] = precio
        
        return tarifas
    
    def calcular_factura_consumo(self, consumoM3, tiene_mora=False):
        """Calcula el monto de una factura basada en consumo de agua"""
        tarifas = self.obtener_tarifas()
        
        subtotal = 0
        mora = 0
        
        # Cuota única si consumo <= 5m³
        if consumoM3 <= 5:
            subtotal = tarifas.get('CUOTA UNICA 1-5m³', 7.00)
        else:
            # Cuota base + m³ adicionales
            subtotal = tarifas.get('CUOTA UNICA 1-5m³', 7.00)
            m3_adicionales = consumoM3 - 5
            subtotal += m3_adicionales * tarifas.get('M³ ADICIONAL', 0.50)
        
        # Mora si aplica
        if tiene_mora:
            mora = tarifas.get('MORA (RECIBO VENCIDO)', 2.00)
        
        total = subtotal + mora
        
        return {
            'subtotal': round(subtotal, 2),
            'mora': round(mora, 2),
            'total': round(total, 2)
        }
    
    def verificar_mora(self, idUsuario):
        """Verifica si el usuario tiene facturas vencidas pendientes"""
        sql = f"""
            SELECT * FROM facturas 
            WHERE idUsuario = {idUsuario} 
            AND estado IN ('Pendiente', 'Vencida')
            AND fechaVencimiento < CURDATE()
        """
        resultado = db.consultar(sql)
        return len(resultado) > 0
    
    def administrar(self, datos):
        """Maneja crear, modificar y eliminar facturas"""
        if datos['accion'] == "generar_desde_lectura":
            # Verificar si ya existe factura
            if self.verificar_factura_existente(datos['idLectura']):
                return "Ya existe una factura para esta lectura"
            
            # Verificar si tiene mora (facturas anteriores vencidas)
            tiene_mora = self.verificar_mora(datos['idUsuario'])
            
            # Calcular montos
            calculo = self.calcular_factura_consumo(datos['consumoM3'], tiene_mora)
            
            # Fecha de emisión y vencimiento
            fecha_emision = date.today()
            fecha_vencimiento = fecha_emision + timedelta(days=30)  # 30 días para pagar
            
            sql = """
                INSERT INTO facturas 
                (idUsuario, idLectura, fechaEmision, fechaVencimiento, tipoFactura, 
                 subtotal, mora, montoTotal, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (
                datos['idUsuario'],
                datos['idLectura'],
                fecha_emision,
                fecha_vencimiento,
                'Consumo Mensual',
                calculo['subtotal'],
                calculo['mora'],
                calculo['total'],
                'Pendiente'
            )
            
            resultado = db.ejecutar(sql, valores)
            
            if resultado == "ok":
                return {"msg": "ok", "montoTotal": calculo['total']}
            else:
                return resultado
        
        elif datos['accion'] == "factura_especial":
            # Para otros servicios (Reconexión, Acometida, etc.)
            fecha_emision = date.today()
            fecha_vencimiento = fecha_emision + timedelta(days=30)
            
            sql = """
                INSERT INTO facturas 
                (idUsuario, idLectura, fechaEmision, fechaVencimiento, tipoFactura, 
                 subtotal, mora, montoTotal, estado)
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (
                datos['idUsuario'],
                fecha_emision,
                fecha_vencimiento,
                datos['tipoFactura'],
                datos['monto'],
                0,  # Sin mora inicial para servicios especiales
                datos['monto'],
                'Pendiente'
            )
            
            return db.ejecutar(sql, valores)
        
        elif datos['accion'] == "eliminar":
            # Solo se pueden eliminar facturas no pagadas
            sql_check = f"SELECT estado FROM facturas WHERE idFactura = {datos['idFactura']}"
            resultado = db.consultar(sql_check)
            
            if len(resultado) > 0 and resultado[0]['estado'] == 'Pagada':
                return "No se puede eliminar una factura pagada"
            
            sql = "DELETE FROM facturas WHERE idFactura = %s"
            valores = (datos['idFactura'],)
            return db.ejecutar(sql, valores)
        
        return "Acción no reconocida"