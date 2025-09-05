from client2 import Client
import threading

def conectarSuma(direccion, puerto):
    client = Client()
    for i in range(20):
        client.connect(direccion, puerto)
        suma= (client.suma(i, i))
        if i % 10 == 0:
            print(suma)

def conectarProducto(direccion, puerto):
    client = Client()
    for i in range(100):
        client.connect(direccion, puerto) 
        producto = client.producto(i, i)
        if i % 10 == 0:
            print(producto)

    
def conectarIncorrecto(direccion, puerto):
    client = Client()
    client.connect(direccion, puerto)
    client.incorrecto()
    
def conectarConcatenar(direccion, puerto):
    client = Client()
    client.connect(direccion, puerto)
    print(client.concatenar("Hola ", "mundo"))


if __name__ == "__main__":
    
    t1 = threading.Thread(target=conectarSuma, args=("127.0.0.1", 12000))
    t2 = threading.Thread(target=conectarProducto, args=("127.0.0.1", 12000))
    t3 = threading.Thread(target=conectarIncorrecto, args=("127.0.0.1", 12000))
    t4 = threading.Thread(target=conectarConcatenar, args=("127.0.0.1", 12000))
    
    t1.start()
    t2.start() 
    t3.start()
    t4.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()

