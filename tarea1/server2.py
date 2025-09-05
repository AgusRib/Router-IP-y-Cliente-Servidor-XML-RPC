from datetime import datetime
from socket import *
import socket
import _socket
import xml.etree.ElementTree as ET
from xmlrpc.client import loads, dumps, Fault


#from socket import *
#serverPort = 12000
#serverSocket = socket(AF_INET,SOCK_STREAM)
#serverSocket.bind((’’,serverPort))
#serverSocket.listen(1)
#print(’The server is ready to receive’)
#while True:
#self.connectionSocket, addr = serverSocket.accept()
#sentence = connectionSocket.recv(10).decode()
#capitalizedSentence = sentence.upper()
#connectionSocket.send(capitalizedSentence.encode())
#connectionSocket.close()

class Server:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.master = None      
        #self.master.bind(("*", 0))
        self.server = None
        self.connectionSocket = None
        self.err = None
        self.methods = {}
        
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

            return method_name, tuple(params)
        except ET.ParseError as e:
            raise Exception from e    
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
            xml += "</value></param></params>"
            
            xml += "</methodResponse>"
        return xml
            
        

    def add_method(self, method):
        self.methods[method.__name__] = method

    def serve(self):
        self.master = socket.socket(AF_INET,SOCK_STREAM)
        self.master.bind((self.address, self.port))
        self.master.listen(1)

        print("Pronto el server para recibir ravioles!")

        while True:
            self.connectionSocket, _ = self.master.accept()
            response = None
            try:
                # Leo las lineas de cabecera hasta encontrar el separador \r\n\r\nd (un retorno de carro y dos enters)
                request = ""
                self.connectionSocket.settimeout(5) # Timeout de 5 segundos para evitar bloqueos indefinidos
                while '\r\n\r\n' not in request:    
                    parte = self.connectionSocket.recv(10)
                    parte = parte.decode()
                    request += parte

                # Busco el Content-Length en las cabeceras
                content_length = 0
                found = False
                headers = request.split('\r\n\r\n')[0]
                for line in headers.split('\r\n'):
                    if not found and 'Content-Length:' in line:
                        content_length = int(line.split(':')[1].strip())
                        found = True
                
                # Leer el body con contentlenght como cond dee parada
                largocuerpo = len(request.split('\r\n\r\n')[1])
                while largocuerpo < content_length:
                    parte = self.connectionSocket.recv(10).decode()
                    if (len(parte) == 0):           
                        break
                    request += parte
                    largocuerpo += len(parte)
                # Unmarshallea el request de XML-RPC a string (lo hace automaticamente loads)
                try:  
                    method_name, params = self.parseRequest(request.split('\r\n\r\n')[1])
                except Exception as e:
                    response = self.construirXML((1, f"Error al parsear XML: {str(e)}"), True)
                else:
                    #Solo sigue si no hubo error de parsing
                    if method_name not in self.methods:
                        response = self.construirXML([2, f"No existe el método: {method_name}"], True)
                    else:
                        try:
                            result = self.methods[method_name](*params)
                            response = self.construirXML(result, False)
                        except TypeError as e:
                            response = self.construirXML((3, f"Error en parámetros del metodo invocado: {str(e)}"), True)
                        except Exception as e:
                            response = self.construirXML((4, f"Error interno en la ejecución del metodo: {str(e)}"), True)

            except Exception as e:
                # Fault 5: Solo si ocurre un error no manejado
                if not response:  # Si no se seteo ninguna response específica
                    response = self.construirXML((5, f"Error del servidor: {str(e)}"), True)

            finally:
                # Enviar la respuesta con el resu o el error
                responsebytes = response.encode()
                ahora = datetime.now()
                ahora = ahora.strftime("%a, %d %b %Y %H:%M:%S GMT")
                formateadohttp = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Date: {ahora}\r\n"
                    "Content-Type: text/xml\r\n"
                    f"Content-Length: {len(responsebytes)}\r\n"
                    "\r\n"
                )
                http_response = formateadohttp.encode() + responsebytes
                total_sent = 0
                while total_sent < len(http_response):
                    sent = self.connectionSocket.send(http_response[total_sent:])
                    total_sent += sent
                print("Respuesta enviada")
                self.connectionSocket.close()

