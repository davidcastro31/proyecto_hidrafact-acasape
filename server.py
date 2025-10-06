from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
from urllib.parse import urlparse, parse_qs
import json 
import crud_login
import crud_usuario

port = 3000

crudLogin = crud_login.crud_login()
crudUsuario = crud_usuario.crud_usuario()

class miServidor(SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parseada = urlparse(self.path)
        path = url_parseada.path
        parametros = parse_qs(url_parseada.query)

        # Redirigir raíz al login
        if self.path == "/":
            self.path = "/modulos/login.html"
            return SimpleHTTPRequestHandler.do_GET(self)
        
        # Obtener usuarios
        if self.path == "/usuarios":
            usuarios = crudUsuario.consultar("")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(usuarios).encode('utf-8'))
            return
        
        # Buscar usuarios
        if path == "/buscar_usuarios":
            buscar = parametros.get('q', [''])[0]
            usuarios = crudUsuario.consultar(buscar)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(usuarios).encode('utf-8'))
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
        elif self.path == "/usuarios":
            resp = {"msg": crudUsuario.administrar(datos)}
        
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