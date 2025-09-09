#curl para probarlo:

#curl -X POST http://127.0.0.1:12000/ \
#  -H "Content-Type: application/json" \
#  -d '{"method": "suma", "params": [3, 5]}'


from server2 import Server

def suma(a, b):
    return a + b


def multiplicar(a, b):
    return a * b

def dividir(a, b):
    if b == 0:
        raise ValueError("No se puede dividir por cero")
    return a/b

def ordenar(numeros):
    return sorted(numeros)
    
def quienEs():
    return "Soy Yo..."



def main():
    server1 = Server("127.0.0.1", 12000)
    server1.add_method(suma)
    server1.add_method(multiplicar)
    server1.add_method(ordenar)
    server1.add_method(dividir)
    server1.add_method(quienEs)
    server1.serve()


    

if __name__ == "__main__":
    main()