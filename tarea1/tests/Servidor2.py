import time
from server2 import Server

def concat(s1,s2):
    return s1 + s2

def sonIguales(s1,s2):
    return s1 == s2

def CantOcurrencias(s1,s2):
    return s1.count(s2)

def concatenameXVeces(n,s):
    for i in range(n):
        s = s + s

    return s

def repetime(s):
    return s

def demorame(s):
    
    time.sleep(10)
    return s

def main():
    server2 = Server("127.0.0.1", 13000)
    server2.add_method(concat)
    server2.add_method(sonIguales)
    server2.add_method(CantOcurrencias)
    server2.add_method(concatenameXVeces)
    server2.add_method(repetime)
    server2.serve()

if __name__ == "__main__":
    main()