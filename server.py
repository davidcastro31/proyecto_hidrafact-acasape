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
import traceback

port = 3000

crudLogin = crud_login.crud_login()
crudUsuario = crud_usuario.crud_usuario()
crudLectura = crud_lectura.crud_lectura()
crudTarifa = crud_tarifa.crud_tarifa()
crudFactura = crud_factura.crud_factura()
crudPago = crud_pago.crud_pago()

class miServidor(SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
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
                try:
                    crudFactura.actualizar_estados_vencidos()
                except Exception:
                    # si no existe el método, ignorar
                    pass
                # Obtener solo pendientes y vencidas
                facturas = crudFactura.consultar_por_usuario(int(idUsuario))
                facturas_pendientes = [f for f in facturas if f.get('estado') in ['Pendiente', 'Vencida']]
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

            # NUEVO: Endpoint agregado - DETALLE DE USUARIO
            if path == "/api/detalle_usuario":
                idUsuario = parametros.get('idUsuario', [0])[0]
                try:
                    idU = int(idUsuario)
                except:
                    idU = 0

                # actualizar estados de facturas vencidas si existe función
                try:
                    crudFactura.actualizar_estados_vencidos()
                except Exception:
                    pass

                # obtener info del usuario: intentar con método específico, si no, filtrar consultar("")
                usuario = None
                try:
                    if hasattr(crudUsuario, 'consultar_por_id'):
                        usuario = crudUsuario.consultar_por_id(idU)
                    elif hasattr(crudUsuario, 'obtener'):
                        usuario = crudUsuario.obtener(idU)
                    else:
                        # fallback: consultar todos y filtrar
                        todos = crudUsuario.consultar("")
                        for u in todos:
                            try:
                                if int(u.get('idUsuario') or u.get('Id_socio') or 0) == idU:
                                    usuario = u
                                    break
                            except:
                                continue
                except Exception:
                    usuario = None

                # facturas
                try:
                    facturas = crudFactura.consultar_por_usuario(idU)
                except Exception:
                    # fallback: consultar todas y filtrar
                    facturas = []
                    try:
                        todas = crudFactura.consultar_todas()
                        facturas = [f for f in todas if int(f.get('idUsuario', f.get('Id_socio', 0))) == idU]
                    except Exception:
                        facturas = []

                # lecturas
                try:
                    lecturas = crudLectura.consultar_por_usuario(idU)
                except Exception:
                    lecturas = []

                # pagos (CORREGIDO: llamar al método correcto del CRUD)
                pagos = []
                try:
                    if hasattr(crudPago, 'consultar_pagos_usuario'):
                        pagos = crudPago.consultar_pagos_usuario(idU)
                    elif hasattr(crudPago, 'consultar_por_usuario'):
                        pagos = crudPago.consultar_por_usuario(idU)
                    elif hasattr(crudPago, 'consultar'):
                        pagos_all = crudPago.consultar("")
                        pagos = [p for p in pagos_all if int(p.get('idUsuario', p.get('Id_socio', 0))) == idU]
                except Exception as e:
                    print("Error al obtener pagos:", e)
                    pagos = []

                # estadísticos
                total_facturas = len(facturas)
                pendientes = [f for f in facturas if f.get('estado') == 'Pendiente']
                vencidas = [f for f in facturas if f.get('estado') == 'Vencida']
                pagadas = [f for f in facturas if f.get('estado') == 'Pagada']

                # morosidad / bloqueo
                try:
                    bloqueado = crudFactura.usuario_bloqueado(idU)
                except Exception:
                    bloqueado = False
                try:
                    total_vencidas = crudFactura.contar_facturas_vencidas(idU)
                except Exception:
                    total_vencidas = len(vencidas)

                # Formatear salida (defensas si usuario es None)
                usuario_out = {
                    "idUsuario": None,
                    "num_contador": None,
                    "nombre": None,
                    "correo": None,
                    "estado": None
                }
                if usuario:
                    # algunos CRUD devuelven claves con distintos nombres, intentamos normalizar
                    usuario_out["idUsuario"] = usuario.get('idUsuario') or usuario.get('Id_socio') or usuario.get('id') or usuario_out["idUsuario"]
                    usuario_out["num_contador"] = usuario.get('num_contador') or usuario.get('numero_medidor') or usuario_out["num_contador"]
                    usuario_out["nombre"] = usuario.get('nombre') or usuario.get('Nombres') or usuario_out["nombre"]
                    usuario_out["correo"] = usuario.get('correo') or usuario.get('email') or usuario_out["correo"]
                    usuario_out["estado"] = usuario.get('estado') or usuario.get('Estado') or usuario_out["estado"]
                else:
                    usuario_out["idUsuario"] = idU

                resp_obj = {
                    "usuario": usuario_out,
                    "facturas": {
                        "total": total_facturas,
                        "pendientes": len(pendientes),
                        "vencidas": len(vencidas),
                        "pagadas": len(pagadas),
                        "detalle": facturas
                    },
                    "lecturas": lecturas,
                    "pagos": pagos,
                    "morosidad": {
                        "es_moroso": total_vencidas > 0,
                        "facturas_vencidas": total_vencidas,
                        "bloqueado": bloqueado
                    }
                }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resp_obj).encode('utf-8'))
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
                    
                    # Endpoint: reportes
            if path == "/api/reportes":
                periodo = parametros.get('periodo', ['mes'])[0]

                try:
                    from datetime import datetime, timedelta

                    # Obtener todos los datos (se intenta usar los métodos existentes)
                    try:
                        usuarios = crudUsuario.consultar("")
                    except Exception:
                        usuarios = []

                    try:
                        facturas = crudFactura.consultar_todas()
                    except Exception:
                        try:
                            facturas = crudFactura.consultar("")
                        except Exception:
                            facturas = []

                    try:
                        pagos = crudPago.consultar_todos_pagos()
                    except Exception:
                        try:
                            pagos = crudPago.consultar_todos()
                        except Exception:
                            try:
                                pagos = crudPago.consultar("")
                            except Exception:
                                pagos = []

                    # Filtrar por período
                    hoy = datetime.now()
                    if periodo == 'hoy':
                        fecha_inicio = hoy.replace(hour=0, minute=0, second=0)
                    elif periodo == 'semana':
                        fecha_inicio = hoy - timedelta(days=7)
                    elif periodo == 'mes':
                        fecha_inicio = hoy - timedelta(days=30)
                    elif periodo == 'anio':
                        fecha_inicio = hoy - timedelta(days=365)
                    else:  # todo
                        fecha_inicio = datetime(2000, 1, 1)

                    # Estadísticas de usuarios
                    total_usuarios = len(usuarios)
                    usuarios_activos = len([u for u in usuarios if u.get('estado') == 'Activo'])

                    # Usuarios morosos y bloqueados
                    morosos = []
                    bloqueados_count = 0
                    deuda_total = 0

                    for usuario in usuarios:
                        facturas_vencidas_usuario = [f for f in facturas
                                                      if f.get('idUsuario') == usuario.get('idUsuario')
                                                      and f.get('estado') == 'Vencida']

                        if len(facturas_vencidas_usuario) > 0:
                            deuda = sum(float(f.get('montoTotal', 0)) for f in facturas_vencidas_usuario)
                            deuda_total += deuda

                            morosos.append({
                                'nombre': usuario.get('nombre'),
                                'num_contador': usuario.get('num_contador'),
                                'facturas_vencidas': len(facturas_vencidas_usuario),
                                'deuda': deuda
                            })

                            if len(facturas_vencidas_usuario) >= 3:
                                bloqueados_count += 1

                    # Ordenar morosos por deuda
                    morosos = sorted(morosos, key=lambda x: x['deuda'], reverse=True)[:10]

                    # Estadísticas de facturas
                    facturas_periodo = []
                    for f in facturas:
                        fecha_str = f.get('fechaEmision')
                        try:
                            if fecha_str and datetime.strptime(fecha_str, '%Y-%m-%d') >= fecha_inicio:
                                facturas_periodo.append(f)
                        except Exception:
                            continue

                    total_facturas = len(facturas_periodo)
                    facturas_pagadas = len([f for f in facturas_periodo if f.get('estado') == 'Pagada'])
                    facturas_pendientes = len([f for f in facturas_periodo if f.get('estado') == 'Pendiente'])
                    facturas_vencidas = len([f for f in facturas_periodo if f.get('estado') == 'Vencida'])

                    monto_pendiente = sum(float(f.get('montoTotal', 0)) for f in facturas_periodo if f.get('estado') == 'Pendiente')
                    monto_vencido = sum(float(f.get('montoTotal', 0)) for f in facturas_periodo if f.get('estado') == 'Vencida')

                    # Ingresos
                    pagos_periodo = []
                    for p in pagos:
                        fecha_p = p.get('fechaPago')
                        try:
                            if fecha_p and datetime.strptime(fecha_p, '%Y-%m-%d') >= fecha_inicio:
                                pagos_periodo.append(p)
                        except Exception:
                            continue

                    total_ingresos = sum(float(p.get('montoPagado', 0)) for p in pagos_periodo)

                    # Ingresos mensuales (últimos 6 meses)
                    meses_labels = []
                    meses_montos = []

                    for i in range(5, -1, -1):
                        mes_fecha = hoy - timedelta(days=i*30)
                        mes_inicio = mes_fecha.replace(day=1)
                        if i > 0:
                            mes_fin = (mes_fecha + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        else:
                            mes_fin = hoy

                        pagos_mes = []
                        for p in pagos:
                            fecha_p = p.get('fechaPago')
                            try:
                                if fecha_p and mes_inicio <= datetime.strptime(fecha_p, '%Y-%m-%d') <= mes_fin:
                                    pagos_mes.append(p)
                            except Exception:
                                continue

                        meses_labels.append(mes_fecha.strftime('%b'))
                        meses_montos.append(sum(float(p.get('montoPagado', 0)) for p in pagos_mes))

                    # Métodos de pago
                    metodos = {}
                    for pago in pagos_periodo:
                        metodo = pago.get('metodoPago', 'Efectivo')
                        if metodo not in metodos:
                            metodos[metodo] = {'cantidad': 0, 'monto': 0}
                        metodos[metodo]['cantidad'] += 1
                        metodos[metodo]['monto'] += float(pago.get('montoPagado', 0))

                    # Consumo de agua (de lecturas)
                    try:
                        from crud_lectura import crud_lectura
                        crudLect = crud_lectura()
                        todas_lecturas = []
                        for usuario in usuarios:
                            try:
                                lecturas = crudLect.consultar_por_usuario(usuario.get('idUsuario'))
                                todas_lecturas.extend(lecturas)
                            except Exception:
                                continue

                        consumos = [float(l.get('consumoM3', 0)) for l in todas_lecturas if l.get('consumoM3')]
                        consumo_total = sum(consumos) if consumos else 0
                        consumo_promedio = consumo_total / len(consumos) if consumos else 0
                        consumo_maximo = max(consumos) if consumos else 0
                        consumo_minimo = min(consumos) if consumos else 0
                    except Exception:
                        consumo_total = 0
                        consumo_promedio = 0
                        consumo_maximo = 0
                        consumo_minimo = 0

                    # Construir respuesta
                    reporte = {
                        'usuarios': {
                            'total': total_usuarios,
                            'activos': usuarios_activos
                        },
                        'ingresos': {
                            'total': total_ingresos
                        },
                        'morosos': {
                            'total': len(morosos),
                            'deuda': deuda_total
                        },
                        'bloqueados': bloqueados_count,
                        'facturas': {
                            'total': total_facturas,
                            'pagadas': facturas_pagadas,
                            'pendientes': facturas_pendientes,
                            'vencidas': facturas_vencidas,
                            'montoPendiente': monto_pendiente,
                            'montoVencido': monto_vencido
                        },
                        'ingresosMensuales': {
                            'meses': meses_labels,
                            'montos': meses_montos
                        },
                        'topMorosos': morosos,
                        'metodosPago': {
                            'metodos': list(metodos.keys()),
                            'cantidades': [metodos[m]['cantidad'] for m in metodos],
                            'montos': [metodos[m]['monto'] for m in metodos]
                        },
                        'consumo': {
                            'total': consumo_total,
                            'promedio': consumo_promedio,
                            'maximo': consumo_maximo,
                            'minimo': consumo_minimo
                        }
                    }

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(reporte).encode('utf-8'))
                    return

                except Exception as e:
                    print(f"Error en reportes: {e}")
                    import traceback
                    traceback.print_exc()
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                    return
            # Cargar módulos HTML
            if path == "/vistas":
                self.path = '/modulos/' + parametros['form'][0] + '.html'
                return SimpleHTTPRequestHandler.do_GET(self)
            
            # Servir archivos estáticos normalmente
            return SimpleHTTPRequestHandler.do_GET(self)

        except Exception as e:
            print("Error en do_GET:", e)
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status":"error", "error": str(e)}).encode('utf-8'))
            return
    
    def do_POST(self):
        try:
            longitud = int(self.headers.get('Content-Length', 0))
            datos = self.rfile.read(longitud) if longitud > 0 else b'{}'
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
                
                if resultado.get('status') == 'ok':
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
        except Exception as e:
            print("Error en do_POST:", e)
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status":"error", "error": str(e)}).encode('utf-8'))


print("=" * 50)
print("Servidor ejecutándose en el puerto", port)
print("Abre tu navegador en: http://localhost:3000")
print("Usuario: admin | Contraseña: admin123")
print("=" * 50)
server = HTTPServer(("localhost", port), miServidor)
server.serve_forever()

