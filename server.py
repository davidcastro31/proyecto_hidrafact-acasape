from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
from urllib.parse import urlparse, parse_qs
import json 
import crud_login
import crud_usuario
import crud_lectura
import crud_tarifa
import crud_factura
import crud_pago
from generador_recibo import generar_pdf_factura
from generador_comprobante import generar_pdf_comprobante
import os

port = 3000

crudLogin = crud_login.crud_login()
crudUsuario = crud_usuario.crud_usuario()
crudLectura = crud_lectura.crud_lectura()
crudTarifa = crud_tarifa.crud_tarifa()
crudFactura = crud_factura.crud_factura()
crudPago = crud_pago.crud_pago()

class miServidor(SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parseada = urlparse(self.path)
        path = url_parseada.path
        parametros = parse_qs(url_parseada.query)

        if self.path == "/":
            self.path = "/modulos/login.html"
            return SimpleHTTPRequestHandler.do_GET(self)
        
        if path == "/api/usuarios":
            usuarios = crudUsuario.consultar("")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(usuarios).encode('utf-8'))
            return

        if path == "/api/buscar_usuarios":
            buscar = parametros.get('q', [''])[0]
            usuarios = crudUsuario.consultar(buscar)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(usuarios).encode('utf-8'))
            return

        if path == "/api/lecturas":
            idUsuario = parametros.get('idUsuario', [0])[0]
            lecturas = crudLectura.consultar_por_usuario(idUsuario)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(lecturas).encode('utf-8'))
            return

        if path == "/api/ultima_lectura":
            idUsuario = parametros.get('idUsuario', [0])[0]
            ultima = crudLectura.obtener_ultima_lectura(idUsuario)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ultima": float(ultima)}).encode('utf-8'))
            return

        if path == "/api/tarifas":
            tarifas = crudTarifa.consultar()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(tarifas).encode('utf-8'))
            return

        if path == "/api/facturas":
            idUsuario = parametros.get('idUsuario', [0])[0]
            if idUsuario and idUsuario != '0':
                facturas = crudFactura.consultar_por_usuario(idUsuario)
            else:
                facturas = crudFactura.consultar_todas()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(facturas).encode('utf-8'))
            return

        # NUEVO: Obtener facturas pendientes/vencidas para pagos
        if path == "/api/facturas_pendientes":
            idUsuario = parametros.get('idUsuario', [0])[0]
            # Actualizar estados primero
            crudFactura.actualizar_estados_vencidos()
            # Obtener solo pendientes y vencidas
            facturas = crudFactura.consultar_por_usuario(int(idUsuario))
            facturas_pendientes = [f for f in facturas if f['estado'] in ['Pendiente', 'Vencida']]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(facturas_pendientes).encode('utf-8'))
            return

        if path == "/api/verificar_factura":
            idLectura = parametros.get('idLectura', [0])[0]
            existe = crudFactura.verificar_factura_existente(idLectura)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"existe": existe}).encode('utf-8'))
            return

        if path == "/api/verificar_bloqueo":
            idUsuario = parametros.get('idUsuario', [0])[0]
            bloqueado = crudFactura.usuario_bloqueado(int(idUsuario))
            total_vencidas = crudFactura.contar_facturas_vencidas(int(idUsuario))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "bloqueado": bloqueado,
                "total_vencidas": total_vencidas
            }).encode('utf-8'))
            return

        # Generar PDF de factura
        if path == "/api/generar_pdf_factura":
            idFactura = int(parametros.get('idFactura', [0])[0])
            try:
                filename = generar_pdf_factura(idFactura, crudFactura, crudUsuario, crudLectura)
                if filename and os.path.exists(filename):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "filename": filename
                    }).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "No se pudo generar el PDF"
                    }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode('utf-8'))
            return

        # Descargar PDF de recibo
        if path.startswith("/recibos/"):
            try:
                filepath = path[1:]
                if os.path.exists(filepath):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/pdf')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
                    self.end_headers()
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            except Exception as e:
                print(f"Error al servir PDF: {e}")

        # NUEVO: Descargar PDF de comprobante
        if path.startswith("/comprobantes/"):
            try:
                filepath = path[1:]
                if os.path.exists(filepath):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/pdf')
                    self.send_header('Content-Disposition', f'inline; filename="{os.path.basename(filepath)}"')
                    self.end_headers()
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            except Exception as e:
                print(f"Error al servir comprobante: {e}")
        
        # Cargar módulos HTML
        if path == "/vistas":
            self.path = '/modulos/' + parametros['form'][0] + '.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        
        # Servir archivos estáticos normalmente
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        longitud = int(self.headers['Content-Length'])
        datos = self.rfile.read(longitud)
        datos = datos.decode("utf-8")
        datos = parse.unquote(datos)
        datos = json.loads(datos)
        
        if self.path == "/login":
            resp = crudLogin.verificar(datos['usuario'], datos['clave'])

        elif self.path == "/api/usuarios":
            resp = {"msg": crudUsuario.administrar(datos)}

        elif self.path == "/api/lecturas":
            resp = {"msg": crudLectura.administrar(datos)}

        elif self.path == "/api/tarifas":
            resp = {"msg": crudTarifa.administrar(datos)}

        elif self.path == "/api/facturas":
            resultado = crudFactura.administrar(datos)
            if isinstance(resultado, dict):
                resp = resultado
            else:
                resp = {"msg": resultado}

        # NUEVO: Registrar pago
        elif self.path == "/api/registrar_pago":
            resultado = crudPago.registrar_pago(datos)
            
            if resultado['status'] == 'ok':
                # Generar comprobante PDF
                try:
                    filename = generar_pdf_comprobante(
                        resultado['idPago'],
                        datos,
                        crudUsuario,
                        crudFactura
                    )
                    resultado['comprobante'] = filename
                except Exception as e:
                    print(f"Error al generar comprobante: {e}")
                    resultado['comprobante'] = None
            
            resp = resultado
        
        else:
            resp = {"status": "error", "msg": "Ruta no encontrada"}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))

print("=" * 50)
print("Servidor ejecutándose en el puerto", port)
print("Abre tu navegador en: http://localhost:3000")
print("Usuario: admin | Contraseña: admin123")
print("=" * 50)
server = HTTPServer(("localhost", port), miServidor)
server.serve_forever()