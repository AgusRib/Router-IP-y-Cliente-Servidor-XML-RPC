from client2 import Client
import threading
import time
import ClienteFalso1
import ClienteFalso2
import ClienteFalso3
import ClienteFalso4
import ClienteFalso5

def test_server1():
    print("Test Server1 de manejo de Enteros")
    client = Client()
    client.connect("127.0.0.1", 12000)
    print("\nTesting Server 1 Puerto 12000:")
    print("-" * 50)

    # Test suma 
    try:
        result = client.suma(5, 3)
        print(f"suma(5, 3) = {result}")
        client.connect("127.0.0.1", 12000)
        
        result2 = client.suma(10, 20)
        print(f"suma(10, 20) = {result2}")
    except Exception as e:
        print(f"Error testing suma: {e}")
    # Test multiplicar 

    try:
        client.connect("127.0.0.1", 12000)
        result = client.multiplicar(4, 5)
        print(f"multiplicar(4, 5) = {result}")
        client.connect("127.0.0.1", 12000)
        result2 = client.multiplicar(7, 6)
        print(f"multiplicar(7, 6) = {result2}")
    except Exception as e:
        print(f"Error testing multiplicar: {e}")
    # Test ordenar 

    try:
        client.connect("127.0.0.1", 12000)
        result = client.ordenar([5, 2, 9, 1])
        print(f"ordenar([5, 2, 9, 1]) = {result}")
        client.connect("127.0.0.1", 12000)
        result2 = client.ordenar([3, 7, 4, 6, 2])
        print(f"ordenar([3, 7, 4, 6, 2]) = {result2}")
    except Exception as e:
        print(f"Error testing ordenar: {e}")
    # Test error cases
    print("\nTesting casos invalidos:")
    print("-" * 50)
    # Test método inexistente





    try:
        client = Client()
        client.connect("127.0.0.1", 12000)
        result = client.metodo_inexistente(1, 2)
        print("Error: método inexistente no lanzó excepción")
    except Exception as e:
        print(f"OK: método inexistente lanzó excepción: {e}")

    # Test parámetros inválidos
    try:
        client.connect("127.0.0.1", 12000)
        result = client.suma("no", 1)
        print("Error: suma con strings no lanzó excepción")
    except Exception as e:
        print(f"OK: suma con strings lanzó excepción: {e}")

    try:
        client.connect("127.0.0.1", 12000)
        result = client.ordenar(1,"america")
        print("Error: ordenar sin lista no lanzó excepción")
    except Exception as e:
        print(f"OK: ordenar sin lista lanzó excepción: {e}")

def test_server2():
    print("Test Server2 de manejo de Strings")
    client = Client()
    client.connect("127.0.0.1", 13000)
    
    print("\nTesting Server 2 puerto 13000:")
    print("-" * 50)
    
    # Test concat 
    try:
        client.connect("127.0.0.1", 13000)
        result = client.concat("Hello, ", "World!")
        print(f'concat("Hello, ", "World!") = {result}')
        client.connect("127.0.0.1", 13000)
        result = client.concat("ROCKAN", "DROLL")
        print(f'concat("ROCKAN", "DROLL") = {result}')
    except Exception as e:
        print(f"Error testing concat: {e}")
    # Test sonIguales 
    try:
        client.connect("127.0.0.1", 13000)
        result = client.sonIguales("test", "test")
        print(f'sonIguales("test", "test") = {result}')
        client.connect("127.0.0.1", 13000)
        result = client.sonIguales("test", "TEST")
        print(f'sonIguales("test", "TEST") = {result}')
    except Exception as e:
        print(f"Error testing sonIguales: {e}")
    # Test CantOcurrencias 
    try:
        client.connect("127.0.0.1", 13000)
        result = client.CantOcurrencias("babanbananbmannab", "an")
        print(f'CantOcurrencias("babanbananbmannab", "an") = {result}')
        client.connect("127.0.0.1", 13000)
        result = client.CantOcurrencias("aaaaaa", "aa")
        print(f'CantOcurrencias("aaaaaa", "aa") = {result}')
    except Exception as e:
        print(f"Error testing CantOcurrencias: {e}")
    
   # Test error cases
    print("\nTesting error cases:")
    print("-" * 50)
    # Test método inexistente
    try:
        client.connect("127.0.0.1", 13000)
        result = client.metodo_inexistente(1, 2)
        print("Error: método inexistente no lanzó excepción")
    except Exception as e:
        print(f"OK: método inexistente lanzó excepción: {e}")
    # Test parámetros inválidos
    try:
        client.connect("127.0.0.1", 13000)
        result = client.concat(123, "paulo")
        print("Error: concat con número y stringg no lanzó excepción",{result})
    except Exception as e:
        print(f"OK: concat con números lanzó excepción: {e}")
    try:
        client.connect("127.0.0.1", 13000)
        result = client.sonIguales("test", 123,33)
        print("Error: sonIguales con 3 parametros no lanzó excepción",{result})
    except Exception as e:
        print(f"OK: sonIguales con 3 parametros lanzó excepción: {e}")
    
    try:
        client.connect("127.0.0.1", 13000)
        result = client.CantOcurrencias("test", 123)
        print("Error: CantOcurrencias con string y número no lanzó excepción",{result})
    except Exception as e:
        print(f"OK: CantOcurrencias con string y número lanzó excepción: {e}")
    

   #Test errores de protocolo HTTP y parseo XML
    print("\nTesting errores de protocolo HTTP y parseo XML:")
    print("-" * 50)
    

    # ClienteFalso1 usa GET en vez de POST
    try:
        clientefalso1 = Client()
        clientefalso1.connect("127.0.0.1",12000)
        resultado = clientefalso1.suma(5,3)
        print("Error: ClienteFalso1 no lanzó excepción al usar GET en vez de POST",{resultado})
    except Exception as e:
        print(f"OK: ClienteFalso1 lanzó excepción al usar GET en vez de POST: {e}")

    #ClienteFalso2 no envía Content-Length
    try:
        clientefalso2=Client()
        clientefalso2.connect("127.0.0.1",12000)
        resultado = clientefalso2.suma(5,3)
        print("Error: ClienteFalso2 no lanzó excepción al no enviar Content-Length",{resultado})
    except Exception as e:
        print(f"OK: ClienteFalso2 lanzó excepción al no enviar Content-Length: {e}")




def main():
    print("Empieza test")
    test_server1()
    test_server2()
    print("\nTest finalizado")

if __name__ == "__main__":
    main()