from datetime import datetime
from socket import *
import socket
import _socket
import xml.etree.ElementTree as ET
import threading

class Server:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.master = None      
        self.server = None
        self.connectionSocket = None
        self.err = None
        self.methods = {}
    
    def construirXML(self, respuesta, esError):
        if esError:
           faultCode = respuesta[0]
           faultString = respuesta[1]
           xml = '<?xml version="1.0"?>'
           xml += "<methodResponse>"
           xml += "<fault><value><struct>"
           
           xml += "<member><name>faultCode</name>"
           xml += "<value><int>{}</int></value></member>".format(faultCode)
           
           xml += "<member><name>faultString</name>"
           xml += "<value><string>{}</string></value></member>".format(faultString)
           
           xml += "</struct></value></fault>"
           xml += "</methodResponse>"

        else:
            xml = '<?xml version="1.0"?>'
            xml += "<methodResponse>"
            
            #Obtengo el tipo de dato de la respuesta y lo agrego al XML
            xml += "<params><param><value>"
            if isinstance(respuesta, int):
                xml += "<int>{}</int>".format(respuesta)
            elif isinstance(respuesta, str):
                xml += "<string>{}</string>".format(respuesta)
            elif isinstance(respuesta, list):
                xml += "<array><data>"
                for item in respuesta:
                    if isinstance(item, int):
                        xml += "<value><int>{}</int></value>".format(item)
                    elif isinstance(item, str):
                        xml += "<value><string>{}</string></value>".format(item)
                    # Agregar más tipos de datos según sea necesario
                xml += "</data></array>"
            elif isinstance(respuesta, float):
                xml += "<double>{}</double>".format(respuesta) 
            xml += "</value></param></params>"
            
            xml += "</methodResponse>"
        return xml

    def parseRequest(self, request):
        try:
            root = ET.fromstring(request)
            method_name = root.find('methodName').text
            params = []
            
            for param in root.findall('.//param/value'):
                if param.find('int') is not None:
                    params.append(int(param.find('int').text))
                elif param.find('string') is not None:
                    params.append(param.find('string').text)
                elif param.find('array') is not None:
                    data = param.find('.//data')
                    items = []
                    for value in data.findall('value'):
                        if value.find('int') is not None:
                            items.append(int(value.find('int').text))
                        elif value.find('string') is not None:
                            items.append(value.find('string').text)
                        # Agregar más tipos de datos según sea necesario
                    params.append(items)
                elif param.find('double') is not None:
                    params.append(float(param.find('double').text))
            return method_name, tuple(params)
        except ET.ParseError as e:
            raise Exception from e
    
    def add_method(self, method):
        self.methods[method.__name__] = method

    def handler_cliente(self, client_socket):
        """Maneja un cliente individual en su propio thread"""
        http_cabezal= "200 OK"
        response = None
        try:
            # Leo las lineas de cabecera
            request = ""
            content_length = 0
            while '\r\n\r\n' not in request:
                client_socket.settimeout(120)
                try:
                  parte = client_socket.recv(10).decode()
                except socket.timeout:
                    if('\r\n\r\n' not in request):
                      http_cabezal= "400 Bad Request"
                      raise Exception("no contiene los dos espacios del formato http")
                    else:  
                        http_cabezal= "408 Timeout"
                        raise Exception("Timeout esperando datos del cliente")
                    
                if not parte: #checkea q no haya cerrau la conección
                    client_socket.close()
                    raise Exception("El cliente cerro la conexion")
                

                request += parte
                

            
             # Verificar que sea método POST
            if not request.startswith('POST'):
                http_cabezal = "501 Not Implemented"
                raise Exception("Solo se acepta método POST")



            # Busco el Content-Length en las cabeceras
            found = False
            headers = request.split('\r\n\r\n')[0]
            for line in headers.split('\r\n'):
                
                if not found and 'Content-Length:' in line:
                   try:
                    content_length = int(line.split(':')[1].strip())
                    found = True
                   except ValueError:
                    http_cabezal= "400 Bad Request"
                    raise Exception("Content-Length no tiene un valor valido")

            if not found:
                http_cabezal= "411 Length Required"
                raise Exception("No se encontro Content-Length en las lineas de cabecera")
            # Leer el body con contentlenght como cond dee parada
            largocuerpo = len(request.split('\r\n\r\n')[1])
            
            while largocuerpo < content_length:
                client_socket.settimeout(120)
                try:
                    parte = client_socket.recv(10).decode()
                except socket.timeout:
                    http_cabezal= "408 Timeout"
                    raise Exception("Timeout esperando datos del cliente")
                
                if not parte: #checkea q no haya cerrau la conección
                    client_socket.close()
                    raise Exception("El cliente cerro la conexion")
                request += parte
                largocuerpo += len(parte)

            # Unmarshallea el request de XML-RPC a string (lo hace automaticamente loads)
            try:  
                
                method_name,params=self.parseRequest(request.split('\r\n\r\n')[1])
                
                
            except Exception as e:
                response = self.construirXML((1, "Error de parseo XML en el servidor: {}".format(str(e))),True)
            else:
                #Solo sigue si no hubo error de parsing
                if method_name not in self.methods:
                    response = self.construirXML((2, "Metodo {} no encontrado".format(method_name)),True)
                    
                else:
                    try:
                        result = self.methods[method_name](*params)
                        response = self.construirXML(result,False)
                    except TypeError as e:
                        response = self.construirXML((3, "Error en los parametros del metodo: {}".format(str(e))),True)
                    except Exception as e:
                        response = self.construirXML((4, "Error al ejecutar el metodo: {}".format(str(e))),True)

        except Exception as e:
            if not response:
               
                response = self.construirXML((5, "Error inesperado en el servidor: {}".format(str(e))),True)

        finally:
            try:

                responsebytes = response.encode()
                ahora=datetime.now()
                ahora=ahora.strftime("%Y-%m-%d %H:%M:%S GMT")
                formateadohttp = (
                    "HTTP/1.0 {}\r\n".format(http_cabezal) +  # <-- espacio agregado
                    "Date: {}\r\n".format(ahora) +
                    "Content-Type: text/xml\r\n" +
                    "Content-Length: {}\r\n".format(len(responsebytes)) +
                    "\r\n"
                )
                http_response = formateadohttp.encode() + responsebytes
                
                total_sent = 0
                while total_sent < len(http_response):
                    sent = client_socket.send(http_response[total_sent:])
                    total_sent+=sent
                print("Respuesta enviada al cliente {}".format(threading.current_thread().name))
            finally:
                client_socket.close()

    def serve(self):
        self.master = socket.socket(AF_INET,SOCK_STREAM)
        self.master.bind((self.address, self.port))
        self.master.listen(20)  # Aumentamos el backlog a 5

        print("Pronto el server para recibir ravioles!")

        while True:
            client_socket, addr = self.master.accept()
            print("Nueva conexión desde {}".format(addr))
            # Crear nuevo thread para manejar el cliente
            client_thread = threading.Thread(
                target=self.handler_cliente,
                args=(client_socket,)
            )
            client_thread.start()

