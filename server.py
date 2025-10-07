from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
from urllib.parse import urlparse, parse_qs
import json 
import crud_login
import crud_usuario
import crud_lectura
import crud_tarifa

port = 3000

crudLogin = crud_login.crud_login()
crudUsuario = crud_usuario.crud_usuario()
crudLectura = crud_lectura.crud_lectura()
crudTarifa = crud_tarifa.crud_tarifa()

class miServidor(SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parseada = urlparse(self.path)
        path = url_parseada.path
        parametros = parse_qs(url_parseada.query)

        # Redirigir raíz al login
        if self.path == "/":
            self.path = "/modulos/login.html"
            return SimpleHTTPRequestHandler.do_GET(self)
        
        # API: Obtener usuarios
        if path == "/api/usuarios":
            usuarios = crudUsuario.consultar("")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(usuarios).encode('utf-8'))
            return
        
        # API: Buscar usuarios
        if path == "/api/buscar_usuarios":
            buscar = parametros.get('q', [''])[0]
            usuarios = crudUsuario.consultar(buscar)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(usuarios).encode('utf-8'))
            return
        
        # API: Obtener lecturas por usuario
        if path == "/api/lecturas":
            idUsuario = parametros.get('idUsuario', [0])[0]
            lecturas = crudLectura.consultar_por_usuario(idUsuario)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(lecturas).encode('utf-8'))
            return
        
        # API: Obtener última lectura
        if path == "/api/ultima_lectura":
            idUsuario = parametros.get('idUsuario', [0])[0]
            ultima = crudLectura.obtener_ultima_lectura(idUsuario)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ultima": float(ultima)}).encode('utf-8'))
            return
        
        # API: Obtener tarifas
        if path == "/api/tarifas":
            tarifas = crudTarifa.consultar()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(tarifas).encode('utf-8'))
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
        
        # Manejar login
        if self.path == "/login":
            resp = crudLogin.verificar(datos['usuario'], datos['clave'])
        
        # Manejar CRUD de usuarios
        elif self.path == "/api/usuarios":
            resp = {"msg": crudUsuario.administrar(datos)}
        
        # Manejar CRUD de lecturas
        elif self.path == "/api/lecturas":
            resp = {"msg": crudLectura.administrar(datos)}
        
        # Manejar modificación de tarifas
        elif self.path == "/api/tarifas":
            resp = {"msg": crudTarifa.modificar(datos)}
        
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