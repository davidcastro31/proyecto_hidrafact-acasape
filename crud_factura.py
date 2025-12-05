import crud_hidrofact
from decimal import Decimal
from datetime import date, timedelta

db = crud_hidrofact.crud()

class crud_factura:
    def actualizar_estados_vencidos(self):
        """Actualiza el estado de facturas vencidas (sin aplicar mora a la misma factura)"""
        try:
            # Solo actualizar el estado de Pendiente a Vencida
            sql_update = """
                UPDATE facturas 
                SET estado = 'Vencida'
                WHERE estado = 'Pendiente' 
                AND fechaVencimiento < CURDATE()
            """
            db.ejecutar(sql_update, ())
                
        except Exception as e:
            print(f"Error al actualizar estados vencidos: {e}")
    
    def contar_facturas_vencidas(self, idUsuario):
        """Cuenta cuántas facturas vencidas tiene un usuario"""
        sql = f"""
            SELECT COUNT(*) as total FROM facturas 
            WHERE idUsuario = {idUsuario} 
            AND estado = 'Vencida'
        """
        resultado = db.consultar(sql)
        if len(resultado) > 0:
            return resultado[0]['total']
        return 0
    
    def usuario_bloqueado(self, idUsuario):
        """Verifica si el usuario está bloqueado por tener 3 o más facturas vencidas"""
        return self.contar_facturas_vencidas(idUsuario) >= 3
    
    def consultar_por_usuario(self, idUsuario):
        """Obtiene todas las facturas de un usuario específico - Ordenadas por ID descendente (más reciente primero)"""
        # Primero actualizar estados vencidos
        self.actualizar_estados_vencidos()
        
        sql = f"""
            SELECT f.*, u.nombre, u.num_contador, u.correo
            FROM facturas f
            INNER JOIN usuarios u ON f.idUsuario = u.idUsuario
            WHERE f.idUsuario = {idUsuario}
            ORDER BY f.idFactura DESC
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
        """Obtiene todas las facturas del sistema - Ordenadas por ID descendente (más reciente primero)"""
        # Primero actualizar estados vencidos
        self.actualizar_estados_vencidos()
        
        sql = """
            SELECT f.*, u.nombre, u.num_contador, u.correo
            FROM facturas f
            INNER JOIN usuarios u ON f.idUsuario = u.idUsuario
            ORDER BY f.idFactura DESC
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
    
    def calcular_factura_consumo(self, consumoM3, cantidad_facturas_vencidas=0):
        """
        Calcula el monto de una factura basada en consumo de agua
        MORA ACUMULATIVA: Se aplica una mora por cada factura vencida
        """
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
        
        # MORA ACUMULATIVA: una mora por cada factura vencida
        if cantidad_facturas_vencidas > 0:
            mora_unitaria = tarifas.get('MORA (RECIBO VENCIDO)', 2.00)
            mora = mora_unitaria * cantidad_facturas_vencidas
        
        total = subtotal + mora
        
        return {
            'subtotal': round(subtotal, 2),
            'mora': round(mora, 2),
            'total': round(total, 2),
            'cantidad_moras': cantidad_facturas_vencidas
        }
    
    def administrar(self, datos):
        """Maneja crear, modificar y eliminar facturas"""
        if datos['accion'] == "generar_desde_lectura":
            # BLOQUEO: Verificar si tiene 3 o más facturas vencidas
            if self.usuario_bloqueado(datos['idUsuario']):
                total_vencidas = self.contar_facturas_vencidas(datos['idUsuario'])
                return f"USUARIO BLOQUEADO: Tiene {total_vencidas} facturas vencidas. Debe pagar al menos una factura vencida antes de generar nuevas facturas."
            
            # Verificar si ya existe factura
            if self.verificar_factura_existente(datos['idLectura']):
                return "Ya existe una factura para esta lectura"
            
            # Contar facturas vencidas para aplicar mora acumulativa
            cantidad_vencidas = self.contar_facturas_vencidas(datos['idUsuario'])
            
            # Calcular montos con mora acumulativa
            calculo = self.calcular_factura_consumo(datos['consumoM3'], cantidad_vencidas)
            
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
                return {
                    "msg": "ok", 
                    "montoTotal": calculo['total'],
                    "mora": calculo['mora'],
                    "cantidad_moras": calculo['cantidad_moras']
                }
            else:
                return resultado
        
        elif datos['accion'] == "factura_especial":
            # BLOQUEO: Verificar si tiene 3 o más facturas vencidas
            if self.usuario_bloqueado(datos['idUsuario']):
                total_vencidas = self.contar_facturas_vencidas(datos['idUsuario'])
                return f"USUARIO BLOQUEADO: Tiene {total_vencidas} facturas vencidas. Debe pagar al menos una factura vencida antes de generar nuevas facturas."
            
            # Para otros servicios (Reconexión, Acometida, etc.)
            # Verificar cantidad de facturas vencidas para mora acumulativa
            cantidad_vencidas = self.contar_facturas_vencidas(datos['idUsuario'])
            
            fecha_emision = date.today()
            fecha_vencimiento = fecha_emision + timedelta(days=30)
            
            # Calcular mora acumulativa si aplica
            tarifas = self.obtener_tarifas()
            mora = 0
            if cantidad_vencidas > 0:
                mora_unitaria = tarifas.get('MORA (RECIBO VENCIDO)', 2.00)
                mora = mora_unitaria * cantidad_vencidas
            
            monto_base = datos['monto']
            monto_total = monto_base + mora
            
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
                monto_base,
                mora,
                monto_total,
                'Pendiente'
            )
            
            resultado = db.ejecutar(sql, valores)
            
            if resultado == "ok":
                return {
                    "msg": "ok",
                    "montoTotal": monto_total,
                    "mora": mora,
                    "cantidad_moras": cantidad_vencidas
                }
            else:
                return resultado
        
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