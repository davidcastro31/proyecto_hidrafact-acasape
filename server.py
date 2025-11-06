from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
from urllib.parse import urlparse, parse_qs
import json 
import crud_login
import crud_usuario
import crud_lectura
import crud_tarifa
import crud_factura

port = 3000

crudLogin = crud_login.crud_login()
crudUsuario = crud_usuario.crud_usuario()
crudLectura = crud_lectura.crud_lectura()
crudTarifa = crud_tarifa.crud_tarifa()
crudFactura = crud_factura.crud_factura()

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

#solo comprobar