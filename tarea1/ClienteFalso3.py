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
#self.client, addr = serverSocket.accept()
#sentence = client.recv(10).decode()
#capitalizedSentence = sentence.upper()
#client.send(capitalizedSentence.encode())
#client.close()

class Client:

    #def __init__(self):
        #self.master = None
        #self.master.bind(("*", 0))
        #self.client = None
       # self.err = None
        #self.address = None
        #self.port = None# 


    #capaz que el connect es init Y connect, lo q pide la letra
    def connect(self, address, port):
        self.master = socket.socket(AF_INET, SOCK_STREAM)
        self.master.connect((address, port))
        self.client = self.master
        self.err = None
        self.address = address
        self.port = port
    #---------------/\ REVISAR /\---------------------
    def construirXML(self, method_name, *args):
        
        xml = "<?xml version='1.0'?>"
        xml += "<methodCall>"
        xml += f"<methodName>{method_name}</methodName>"
        xml += "<params>"
        for arg in args:
            xml += "<param><value>"
            if isinstance(arg, int):
                xml += f"<int>{arg}</int>"
            elif isinstance(arg, str):
                xml += f"<string>{arg}</string>"
            # Agregar más tipos de datos según sea necesario
            elif isinstance(arg, list):
                xml += "<array><data>"
                for item in arg:
                    if isinstance(item, int):
                        xml += f"<value><int>{item}</int></value>"
                    elif isinstance(item, str):
                        xml += f"<value><string>{item}</string></value>"
                    # Agregar más tipos de datos según sea necesario
                xml += "</data></array>"
            xml += "</value></param>"
        xml += "</params>"
        xml += "</methodCall>"
        return xml

    def parseResponse(self, response):
        root = ET.fromstring(response)
        if root.find('.//fault') is not None:
            fault = root.find('.//fault/value/struct')
            fault_code = int(fault.find(".//member[name='faultCode']/value/int").text)
            fault_string = fault.find(".//member[name='faultString']/value/string").text
            raise Exception(fault_code, fault_string)
        else:
            params = root.findall('.//params/param/value')
            param = params[0]
            if param.find('int') is not None:
                return int(param.find('int').text)
            elif param.find('string') is not None:
                return param.find('string').text
            elif param.find('array') is not None:
                data = param.find('.//data')
                items = []
                for value in data.findall('value'):
                    if value.find('int') is not None:
                        items.append(int(value.find('int').text))
                    elif value.find('string') is not None:
                        items.append(value.find('string').text)
                    # Agregar más tipos de datos según sea necesario
                return items
            


    def __getattr__(self, name): #checkear si es lo mas conveniente, si no pudeo directamente implementar todo en el getattr o su alternativa
        def method(*args):
            return self.call_method(name, *args)
        return method #entiendo que la idea es terminarlo dps de un solo uso, no se si es asi, pero iria aca un:
        #clientSocket.close()

    def call_method(self, method_name, *args):
        errparseo=0
        fault1234=0
        # Creo el respuesta XML-RPC----------
        envio_xml = self.construirXML(method_name, *args)

        # Agregamos el formato HTTP
        envio_xmlBytes = envio_xml.encode()
        formateadohttp = (
            "POST /RPC2 HTTP/1.0\r\n"
            "User-Agent: fedora/28.5.04 (Fedora42)\r\n"
            f"Host: {self.address}:{self.port}\r\n"
            "Content-Type: text/xml\r\n"
            "
            "\r\n"
        )
        envio_http = formateadohttp.encode() + envio_xmlBytes
        #-----------------------------------

        # Enviamo --------------------------
        total_sent = 0
        while total_sent < len(envio_http):
          sent = self.client.send(envio_http[total_sent:])
          total_sent += sent
        #-----------------------------------        

        # Recibimo -------------------------
        try:
            # Leo las lineas de cabecera hasta encontrar el separador \r\n\r\nd (un retorno de carro y dos enters)
            respuesta = ""
            content_length = 0
            while '\r\n\r\n' not in respuesta:
                parte = self.client.recv(10).decode()
                respuesta += parte
            
            # Busco el Content-Length en las cabeceras
            found = False
            headers = respuesta.split('\r\n\r\n')[0]
             
            for line in headers.split('\r\n'):
                if not found and 'Content-Length:' in line:
                    content_length = int(line.split(':')[1].strip())
                    found = True
            
            # Leer el body con contentlenght como cond de parada
            largocuerpo = len(respuesta.split('\r\n\r\n')[1])
            
            while largocuerpo < content_length:
                parte = self.client.recv(10).decode()
                respuesta += parte

                largocuerpo += len(parte)
            
            # Unmarshallea el respuesta de XML-RPC a string
            try:  
                resultado = self.parseResponse(respuesta.split('\r\n\r\n')[1])
                
                    
                return resultado  # Si no es fault, retornar el resultado
            except Exception as e:
                
                fault1234=1
                raise Exception(str(e))
            except xml.parsers.expat.ExpatError as e:
                # Error específico de parseo XML en el cliente
                errparseo=1
                raise Exception(1, f"Error de parseo XML en el cliente: {str(e)}")
                
        except Exception as e:
            if fault1234==1 or errparseo==1:
                raise
                # Re-raise faults del servidor sin modificar
        
            # Error imprevisto en el cliente
            raise Exception(5, f"Error inesperado en el cliente: {str(e)}")
