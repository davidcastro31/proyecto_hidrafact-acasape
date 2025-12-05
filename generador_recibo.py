from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
import os
import crud_factura

class GeneradorRecibo:
    def __init__(self):
        self.width, self.height = letter
        
    def generar_recibo(self, factura_data, usuario_data, lectura_data=None):
        """
        Genera un PDF con dos copias del recibo
        factura_data: dict con datos de la factura
        usuario_data: dict con datos del usuario
        lectura_data: dict con datos de la lectura (opcional)
        """
        # Crear carpeta para recibos si no existe
        if not os.path.exists('recibos'):
            os.makedirs('recibos')
        
        filename = f'recibos/recibo_{factura_data["idFactura"]}_{usuario_data["num_contador"]}.pdf'
        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para el encabezado
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=0,
            alignment=TA_CENTER
        )
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Obtener cantidad de facturas vencidas
        crudFact = crud_factura.crud_factura()
        facturas_vencidas = crudFact.contar_facturas_vencidas(usuario_data['idUsuario'])
        
        # Generar COPIA ORIGINAL (Sistema)
        elements.extend(self._crear_recibo_individual(
            factura_data, usuario_data, lectura_data, 
            "ORIGINAL: SISTEMA", styles, header_style, title_style, facturas_vencidas
        ))
        
        # Salto de página
        elements.append(PageBreak())
        
        # Generar COPIA (Usuario)
        elements.extend(self._crear_recibo_individual(
            factura_data, usuario_data, lectura_data, 
            "COPIA: USUARIO", styles, header_style, title_style, facturas_vencidas
        ))
        
        # Construir el PDF
        doc.build(elements)
        return filename
    
    def _crear_recibo_individual(self, factura_data, usuario_data, lectura_data, tipo_copia, styles, header_style, title_style, facturas_vencidas):
        """Crea una copia individual del recibo"""
        elements = []
        
        # === ENCABEZADO ===
        elements.append(Paragraph("RECIBO DE INGRESO", title_style))
        elements.append(Paragraph(
            "ASOCIACION COMUNAL ADMINISTRADORA DEL SISTEMA DE AGUA POTABLE<br/>"
            "EL ENCANTO (ACASAPE) DIST. JIQUILISCO, DPTO. USULUTAN OESTE",
            header_style
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        # === INFORMACIÓN DEL USUARIO ===
        info_usuario = [
            ['CODIGO:', usuario_data['num_contador'], 'N. RECIBO:', str(factura_data['idFactura'])],
            ['USUARIO/A:', usuario_data['nombre'], '', '']
        ]
        
        if lectura_data:
            info_usuario.append([
                'CONTADOR:', usuario_data['num_contador'],
                'LECTURA ACTUAL m³', 'LECTURA ANTERIOR m³', 'CONSUMO m³'
            ])
            info_usuario.append([
                'FECHA DE RECIBO:', factura_data['fechaEmision'],
                str(lectura_data.get('lecturaActual', '')),
                str(lectura_data.get('lecturaAnterior', '')),
                str(lectura_data.get('consumoM3', ''))
            ])
        else:
            info_usuario.append([
                'CONTADOR:', usuario_data['num_contador'], '', ''
            ])
            info_usuario.append([
                'FECHA DE RECIBO:', factura_data['fechaEmision'], '', ''
            ])
        
        tabla_usuario = Table(info_usuario, colWidths=[1.2*inch, 2*inch, 1.3*inch, 1.3*inch])
        tabla_usuario.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
        ]))
        elements.append(tabla_usuario)
        elements.append(Spacer(1, 0.2*inch))
        
        # === DETALLE DE COBRO ===
        detalle_datos = [
            ['CODIGO', 'DESCRIPCION', 'CANTIDAD', 'PRECIO UNITARIO', 'PRECIO TOTAL']
        ]
        
        # Agregar items según el tipo de factura
        if lectura_data and lectura_data.get('consumoM3', 0) > 0:
            consumo = float(lectura_data['consumoM3'])
            
            # Cuota única (1-5m³)
            detalle_datos.append([
                '1',
                'CUOTA UNICA 1-5m³',
                '1',
                f"$ {7.00:.2f}",
                f"$ {7.00:.2f}"
            ])
            
            # M³ adicionales si hay
            if consumo > 5:
                m3_adicionales = consumo - 5
                precio_adicional = m3_adicionales * 0.50
                detalle_datos.append([
                    '2',
                    'M³ ADICIONAL',
                    str(int(m3_adicionales)),
                    f"$ {0.50:.2f}",
                    f"$ {precio_adicional:.2f}"
                ])
        else:
            # Factura especial (otros servicios)
            detalle_datos.append([
                '1',
                factura_data['tipoFactura'],
                '1',
                f"$ {float(factura_data['subtotal']):.2f}",
                f"$ {float(factura_data['subtotal']):.2f}"
            ])
        
        # Agregar mora si existe (puede ser múltiple)
        if float(factura_data.get('mora', 0)) > 0:
            mora_total = float(factura_data['mora'])
            detalle_datos.append([
                '3',
                f'MORA POR {facturas_vencidas} RECIBO(S) VENCIDO(S)',
                str(facturas_vencidas),
                f"$ {2.00:.2f}",
                f"$ {mora_total:.2f}"
            ])
        
        tabla_detalle = Table(detalle_datos, colWidths=[0.8*inch, 2.5*inch, 1*inch, 1.3*inch, 1.3*inch])
        tabla_detalle.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tabla_detalle)
        elements.append(Spacer(1, 0.2*inch))
        
        # === TOTAL A PAGAR ===
        total_datos = [
            ['TOTAL A PAGAR', f"$ {float(factura_data['montoTotal']):.2f}"]
        ]
        tabla_total = Table(total_datos, colWidths=[5.2*inch, 1.3*inch])
        tabla_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tabla_total)
        elements.append(Spacer(1, 0.2*inch))
        
        # === FECHA DE VENCIMIENTO ===
        vencimiento_datos = [
            ['FECHA DE VENCIMIENTO', factura_data['fechaVencimiento']],
            [tipo_copia, '']
        ]
        tabla_vencimiento = Table(vencimiento_datos, colWidths=[3.5*inch, 3*inch])
        tabla_vencimiento.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen if tipo_copia == "ORIGINAL: SISTEMA" else colors.lightyellow),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tabla_vencimiento)
        
        # === ADVERTENCIAS DE MOROSIDAD ===
        elements.append(Spacer(1, 0.3*inch))
        
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Bold',
            leading=12
        )
        
        # ADVERTENCIA SEGÚN CANTIDAD DE FACTURAS VENCIDAS
        if facturas_vencidas >= 3:
            # USUARIO BLOQUEADO - SUSPENSIÓN INMINENTE
            elements.append(Paragraph(
                f"<b>⚠️ ADVERTENCIA CRÍTICA: SUSPENSIÓN DE SERVICIO</b><br/>"
                f"Usted tiene {facturas_vencidas} facturas vencidas sin pagar. "
                f"De acuerdo con nuestras políticas, el servicio de agua será SUSPENDIDO "
                f"si no realiza el pago de al menos una factura vencida. "
                f"Evite la suspensión del servicio pagando sus facturas pendientes a la brevedad.",
                warning_style
            ))
        elif facturas_vencidas == 2:
            # DOS FACTURAS VENCIDAS - ADVERTENCIA FUERTE
            elements.append(Paragraph(
                f"<b>⚠️ ADVERTENCIA IMPORTANTE:</b><br/>"
                f"Usted tiene {facturas_vencidas} facturas vencidas. "
                f"Si acumula 3 o más facturas sin pagar, su servicio de agua será SUSPENDIDO. "
                f"Por favor, ponga al día sus pagos para evitar la suspensión del servicio.",
                warning_style
            ))
        elif facturas_vencidas == 1:
            # UNA FACTURA VENCIDA - ADVERTENCIA LEVE
            elements.append(Paragraph(
                f"<b>⚠️ AVISO:</b> Usted tiene 1 factura vencida sin pagar. "
                f"Recuerde que si acumula 3 facturas vencidas, su servicio será suspendido. "
                f"Le recomendamos ponerse al día con sus pagos.",
                warning_style
            ))
        else:
            # SIN MORA - MENSAJE POSITIVO
            elements.append(Paragraph(
                "✅ Su cuenta está al día. Gracias por su puntualidad en los pagos.",
                ParagraphStyle(
                    'Positive',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.darkgreen,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )
            ))
        
        return elements

# Función auxiliar para usar en server.py
def generar_pdf_factura(idFactura, crudFactura, crudUsuario, crudLectura):
    """
    Genera el PDF de una factura específica
    Retorna el nombre del archivo generado
    """
    try:
        # Obtener datos de la factura
        facturas = crudFactura.consultar_todas()
        factura = None
        for f in facturas:
            if f['idFactura'] == idFactura:
                factura = f
                break
        
        if not factura:
            return None
        
        # Obtener datos del usuario
        usuarios = crudUsuario.consultar("")
        usuario = None
        for u in usuarios:
            if u['idUsuario'] == factura['idUsuario']:
                usuario = u
                break
        
        if not usuario:
            return None
        
        # Obtener datos de lectura si existe
        lectura = None
        if factura.get('idLectura'):
            lecturas = crudLectura.consultar_por_usuario(factura['idUsuario'])
            for l in lecturas:
                if l['idLectura'] == factura['idLectura']:
                    lectura = l
                    break
        
        # Generar el PDF
        generador = GeneradorRecibo()
        filename = generador.generar_recibo(factura, usuario, lectura)
        
        return filename
        
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return None