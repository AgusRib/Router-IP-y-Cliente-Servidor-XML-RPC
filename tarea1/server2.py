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
           xml += f"<value><int>{faultCode}</int></value></member>"
           
           xml += "<member><name>faultString</name>"
           xml += f"<value><string>{faultString}</string></value></member>"
           
           xml += "</struct></value></fault>"
           xml += "</methodResponse>"

        else:
            xml = '<?xml version="1.0"?>'
            xml += "<methodResponse>"
            
            #Obtengo el tipo de dato de la respuesta y lo agrego al XML
            xml += "<params><param><value>"
            if isinstance(respuesta, int):
                xml += f"<int>{respuesta}</int>"
            elif isinstance(respuesta, str):
                xml += f"<string>{respuesta}</string>"
            elif isinstance(respuesta, list):
                xml += "<array><data>"
                for item in respuesta:
                    if isinstance(item, int):
                        xml += f"<value><int>{item}</int></value>"
                    elif isinstance(item, str):
                        xml += f"<value><string>{item}</string></value>"
                    # Agregar más tipos de datos según sea necesario
                xml += "</data></array>"
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

            return method_name, tuple(params)
        except ET.ParseError as e:
            raise Exception from e
    
    def add_method(self, method):
        self.methods[method.__name__] = method

    def handler_cliente(self, client_socket):
        """Maneja un cliente individual en su propio thread"""
        client_socket.settimeout(30)  
        http_cabezal= "200 OK"
        response = None
        try:
            # Leo las lineas de cabecera
            request = ""
            content_length = 0
            while '\r\n\r\n' not in request:
                parte = client_socket.recv(10).decode()
                request += parte
                if len(request)>4096 and '\r\n\r\n' not in request:
                    http_cabezal= "400 Bad Request"
                    raise Exception("Header demasiado grande o no contiene los dos espacios del formato http")

            
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
                parte = client_socket.recv(10).decode()
                request += parte
                largocuerpo += len(parte)

            # Unmarshallea el request de XML-RPC a string (lo hace automaticamente loads)
            try:  
                
                method_name,params=self.parseRequest(request.split('\r\n\r\n')[1])
                
                
            except Exception as e:
                response = self.construirXML((1, f"Error de parseo XML en el servidor: {str(e)}"),True)
            else:
                #Solo sigue si no hubo error de parsing
                if method_name not in self.methods:
                    response = self.construirXML((2, f"Metodo {method_name} no encontrado"),True)
                    print(response)
                else:
                    try:
                        result = self.methods[method_name](*params)
                        print (f"Resultado del metodo {method_name} con parametros {params} es {result} en el thread {threading.current_thread().name}")
                        response = self.construirXML(result,False)
                        print (f"Response construido: {response} en el thread {threading.current_thread().name}")
                    except TypeError as e:
                        response = self.construirXML((3, f"Error en los parametros del metodo: {str(e)}"),True)
                    except Exception as e:
                        response = self.construirXML((4, f"Error al ejecutar el metodo: {str(e)}"),True)

        except Exception as e:
            if not response:
               
                response = self.construirXML((5, f"Error inesperado en el servidor: {str(e)}"),True)

        finally:
            try:
                print(response)
                responsebytes = response.encode()
                ahora=datetime.now()
                ahora=ahora.strftime("%Y-%m-%d %H:%M:%S GMT")
                formateadohttp = (
                    f"HTTP/1.1 {http_cabezal}\r\n"
                    f"Date: {ahora}\r\n"
                    "Content-Type: text/xml\r\n"
                    f"Content-Length: {len(responsebytes)}\r\n"
                    "\r\n"
                )
                http_response = formateadohttp.encode() + responsebytes
                
                total_sent = 0
                while total_sent < len(http_response):
                    sent = self.connectionSocket.send(http_response[total_sent:])
                    total_sent+=sent

            finally:
                client_socket.close()

    def serve(self):
        self.master = socket.socket(AF_INET,SOCK_STREAM)
        self.master.bind((self.address, self.port))
        self.master.listen(20)  # Aumentamos el backlog a 5

        print("Pronto el server para recibir ravioles!")

        while True:
            client_socket, addr = self.master.accept()
            print(f"Nueva conexión desde {addr}")
            # Crear nuevo thread para manejar el cliente
            client_thread = threading.Thread(
                target=self.handler_cliente,
                args=(client_socket,)
            )
            client_thread.start()

