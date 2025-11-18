from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

class GeneradorComprobante:
    def __init__(self):
        self.width, self.height = letter
        
    def generar_comprobante(self, pago_data, usuario_data, facturas_pagadas):
        """
        Genera un PDF de comprobante de pago
        pago_data: dict con datos del pago
        usuario_data: dict con datos del usuario
        facturas_pagadas: list de facturas que se pagaron
        """
        # Crear carpeta para comprobantes si no existe
        if not os.path.exists('comprobantes'):
            os.makedirs('comprobantes')
        
        filename = f'comprobantes/comprobante_{pago_data["idPago"]}_{usuario_data["num_contador"]}.pdf'
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.white,
            spaceAfter=5,
            spaceBefore=10,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            backColor=colors.HexColor('#0d6efd'),
            leftIndent=10,
            rightIndent=10
        )
        
        # === ENCABEZADO ===
        elements.append(Paragraph("Comprobante de Pago", title_style))
        elements.append(Paragraph(
            "ASOCIACIÓN COMUNAL ADMINISTRADORA DEL SISTEMA DE AGUA POTABLE<br/>"
            "EL ENCANTO (ACASAPE)",
            subtitle_style
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        # === DATOS DEL USUARIO ===
        elements.append(Paragraph("Datos del Usuario", section_title_style))
        datos_usuario = [
            ['Nombre:', usuario_data['nombre']],
            ['N° Contador:', usuario_data['num_contador']],
            ['Correo:', usuario_data.get('correo', 'No registrado')]
        ]
        
        tabla_usuario = Table(datos_usuario, colWidths=[2*inch, 4.5*inch])
        tabla_usuario.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0d6efd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(tabla_usuario)
        elements.append(Spacer(1, 0.2*inch))
        
        # === SEGUIMIENTO ===
        elements.append(Paragraph("Seguimiento", section_title_style))
        fecha_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        seguimiento_data = [
            ['Código de Pago:', f"ACASAPE-{str(pago_data['idPago']).zfill(6)}"],
            ['Fecha:', fecha_hora],
            ['Referencia:', f"REF-{usuario_data['num_contador']}-{datetime.now().strftime('%Y%m%d')}"],
        ]
        
        tabla_seguimiento = Table(seguimiento_data, colWidths=[2*inch, 4.5*inch])
        tabla_seguimiento.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0d6efd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(tabla_seguimiento)
        elements.append(Spacer(1, 0.2*inch))
        
        # === DATOS DE LA TRANSACCIÓN ===
        elements.append(Paragraph("Datos de la Transacción", section_title_style))
        transaccion_data = [
            ['Monto:', f"$ {pago_data['montoTotal']:.2f}"],
            ['Método de Pago:', pago_data['metodoPago']],
        ]
        
        tabla_transaccion = Table(transaccion_data, colWidths=[2*inch, 4.5*inch])
        tabla_transaccion.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0d6efd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(tabla_transaccion)
        elements.append(Spacer(1, 0.2*inch))
        
        # === DETALLE DEL PAGO ===
        elements.append(Paragraph("Detalle del Pago", section_title_style))
        
        detalle_data = [
            ['Descripción', 'Monto']
        ]
        
        total = 0
        for factura in facturas_pagadas:
            descripcion = f"{factura['tipoFactura']} - Factura #{factura['idFactura']}"
            monto = float(factura['montoTotal'])
            total += monto
            detalle_data.append([descripcion, f"$ {monto:.2f}"])
        
        tabla_detalle = Table(detalle_data, colWidths=[4.5*inch, 2*inch])
        tabla_detalle.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(tabla_detalle)
        elements.append(Spacer(1, 0.2*inch))
        
        # === TOTAL PAGADO ===
        total_data = [
            ['Total pagado:', f"$ {total:.2f}"]
        ]
        
        tabla_total = Table(total_data, colWidths=[4.5*inch, 2*inch])
        tabla_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(tabla_total)
        elements.append(Spacer(1, 0.3*inch))
        
        # === NOTA FINAL ===
        nota_style = ParagraphStyle(
            'Nota',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        elements.append(Paragraph(
            "Este comprobante es válido como constancia de pago.<br/>"
            "Gracias por su puntualidad en el pago.",
            nota_style
        ))
        
        # Construir el PDF
        doc.build(elements)
        return filename

# Función auxiliar para usar en server.py
def generar_pdf_comprobante(idPago, pago_data, crudUsuario, crudFactura):
    """
    Genera el PDF de un comprobante de pago
    Retorna el nombre del archivo generado
    """
    try:
        # Obtener datos del usuario
        usuarios = crudUsuario.consultar("")
        usuario = None
        for u in usuarios:
            if u['idUsuario'] == pago_data['idUsuario']:
                usuario = u
                break
        
        if not usuario:
            return None
        
        # Obtener datos de las facturas pagadas
        facturas_pagadas = []
        for idFactura in pago_data['facturas']:
            facturas = crudFactura.consultar_todas()
            for f in facturas:
                if f['idFactura'] == idFactura:
                    facturas_pagadas.append(f)
                    break
        
        # Preparar datos del pago
        pago_info = {
            'idPago': idPago,
            'montoTotal': pago_data['montoTotal'],
            'metodoPago': pago_data['metodoPago']
        }
        
        # Generar el PDF
        generador = GeneradorComprobante()
        filename = generador.generar_comprobante(pago_info, usuario, facturas_pagadas)
        
        return filename
        
    except Exception as e:
        print(f"Error al generar comprobante: {e}")
        return None