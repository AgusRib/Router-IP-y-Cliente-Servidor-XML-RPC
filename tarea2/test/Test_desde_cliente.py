from client2 import Client
import threading
import time
#from lorem_text import lorem
#from ClienteFalso1 import ClienteFalso1
#from ClienteFalso2 import Cliente2
#from ClienteFalso3 import ClienteFalso3
#from ClienteFalso4 import ClienteFalso4
#from ClienteFalso5 import ClienteFalso5
import random


def generate_lorem_words(num_words):
    words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", "sed", "do", "eiusmod"]
    return " ".join(random.choices(words, k=num_words))


def test_ICMP(): #==========================================
    print("Test manejo de errores ICMP")
    client = Client()
    client.connect("150.150.0.2", 12000)
    print("\nTesting Server 1 Puerto 12000:")
    print("-" * 50)

    # Test destination net unreachable 

    try:
        client.connect("285.402.0.2", 12000) #esto deberia hacerlo saltar
        result = client.multiplicar(4, 5)
        print(f"multiplicar(4, 5) = {result}")
        client.connect("150.150.0.2", 12000)
        result2 = client.multiplicar(7, 6)
        print(f"multiplicar(7, 6) = {result2}")
    except Exception as e:
        print(f"OK destination net unreachable: {e}")
    
    # Test port unreachable
    try:
        client.connect("100.0.0.50", 12000) # esto debeia hacerlo saltar
        result = client.ordenar([5, 2, 9, 1])
        print(f"ordenar([5, 2, 9, 1]) = {result}")
        client.connect("150.150.0.2", 12000)
        result2 = client.ordenar([3, 7, 4, 6, 2])
        print(f"ordenar([3, 7, 4, 6, 2]) = {result2}")
    except Exception as e:
        print(f"OK port unreachable: {e}")

    
"""def test_ping(): #==========================================
    print("Test manejo de ping desde el cliente")
    client = Client()
    client.connect("100.100.0.2", 13000)
    print("\nTesting Server 2 puerto 13000:")
    print("-" * 50)
    
    try:
        result = client.ping()
        print(f"Ping exitoso: {result}")
    except Exception as e:
        print(f"Error en ping: {e}")"""


def main():
    print("Empieza test")
    time.sleep(2)
    test_ICMP()
    print("\nTest finalizado")

if __name__ == "__main__":
    main()