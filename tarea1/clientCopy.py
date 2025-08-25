from socket import *
import socket
import xml.etree.ElementTree as ET


    #serverName = ’servername’
    #serverPort = 12000
    #clientSocket = socket(AF_INET, SOCK_STREAM)
    #clientSocket.connect((serverName,serverPort))
    #sentence = input(’Input lowercase sentence:’)
    #clientSocket.send(sentence.encode())
    #modifiedSentence = clientSocket.recv(1024)
    #print(’From Server: ’, modifiedSentence.decode())
    #clientSocket.close()

class Client:

    #acorde al curso--------------------
    def __init__(self):
        self.master = None
        #self.master.bind(("*", 0))
        self.client = None
        self.err = None

    def connect(self, address, port):
        self.master = socket(AF_INET, SOCK_STREAM)
        self.master.bind(("*", 0))
        self.client, self.err = self.master.connect((address, port))
    #-----------------------------------

    def andar(self):
        sentence = input('Input lowercase sentence:')

        self.cliente.send(sentence.encode())
        modifiedSentence, self.err = self.cliente.recv(1024)
        print('From Server: ', modifiedSentence.decode())
        self.cliente.close()