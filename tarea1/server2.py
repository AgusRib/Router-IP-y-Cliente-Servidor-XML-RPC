from socket import *
import socket
import _socket
import xml.etree.ElementTree as ET
from xmlrpc.client import loads, dumps, Fault
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
                params, method_name = loads(request.split('\r\n\r\n')[1])
            except Exception as e:
                response = dumps(Fault(1, f"Error al parsear XML: {str(e)}"), methodresponse=True)#dumps marshallea la respuesta a XML
            else:
                #Solo sigue si no hubo error de parsing
                if method_name not in self.methods:
                    response = dumps(Fault(2, f"No existe el metodo: {method_name}"), methodresponse=True)
                else:
                    try:
                        result = self.methods[method_name](*params)
                        response = dumps((result,), methodresponse=True)
                    except TypeError as e:
                        response = dumps(Fault(3, f"Error en parametros del metodo invocado: {str(e)}"), methodresponse=True)
                    except Exception as e:
                        response = dumps(Fault(4, f"Error interno en la ejecucion del metodo: {str(e)}"), methodresponse=True)

        except Exception as e:
            if not response:
                response = dumps(Fault(5, f"Error del servidor: {str(e)}"), methodresponse=True)

        finally:
            try:
        
                responsebytes = response.encode()
                formateadohttp = (
                    f"HTTP/1.1 {http_cabezal}\r\n"
                    "Content-Type: text/xml\r\n"
                    f"Content-Length: {len(responsebytes)}\r\n"
                    "\r\n"
                )
                http_response = formateadohttp.encode() + responsebytes
                
                remaining = http_response
                while remaining:
                    sent = client_socket.send(remaining)
                    remaining = remaining[sent:]
                print(f"Respuesta enviada al cliente {threading.current_thread().name}")
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

