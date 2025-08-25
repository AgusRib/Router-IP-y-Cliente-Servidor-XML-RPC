from socket import *
import socket
import _socket
import xmlrpc
from xmlrpc import parse_request, generate_response 

#from socket import *
#serverPort = 12000
#serverSocket = socket(AF_INET,SOCK_STREAM)
#serverSocket.bind((’’,serverPort))
#serverSocket.listen(1)
#print(’The server is ready to receive’)
#while True:
#self.connectionSocket, addr = serverSocket.accept()
#sentence = connectionSocket.recv(1024).decode()
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


    def add_method(self, method):
        self.methods[method.__name__] = method

    def serve(self):

        self.master = socket(AF_INET,SOCK_STREAM)
        self.master.bind(self.address, self.port)
        self.server = self.master.listen(1)

        print("Pronto el server para recibir ravioles!")

        while True:
            self.connectionSocket, self.err = self.server.accept()

            while self.err!="closed":
                request, self.err = self.connectionSocket.recv(1024).decode()

            sentence = self.connectionSocket.recv(1024).decode()
            capitalizedSentence = sentence.upper()
            self.connectionSocket.send(capitalizedSentence.encode())
            self.connectionSocket.close()
            print("Ravioles servidos!")

