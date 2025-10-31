

#!/usr/bin/env python3
import subprocess
import time

hosts = {
    "client": "client2",
    "servers": ["150.150.0.2", "100.100.0.2"],
    "routers": ["100.0.0.50", "200.200.0.1"]
}


def test_ICMP_ping_traceroute_server():

    print("Test para checkear los msjes ICMP 'Time exceeded', 'Echo request' y 'Echo reply'\n"
    "mediante traceroute y ping, respectivamente, desde el cliente a los servidores.")

    for srv in hosts["servers"]:
        print(f"\n--- PING {srv} ---")
        cmd = f"client ping -c 3 {srv}"
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(resultado.stdout)

        print(f"\n--- TRACEROUTE {srv} ---")
        cmd = f"client traceroute -n {srv}"
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(resultado.stdout)

def test_ICMP_ping_traceroute_router():

    print("\nTest para checkear los msjes ICMP 'Time exceeded', 'Echo request' y 'Echo reply'\n"
    "mediante traceroute y ping, respectivamente, desde el cliente al router.")

    for rtr in hosts["routers"]:
        print(f"\n--- PING {rtr} ---")
        cmd = f"client ping -c 3 {rtr}"
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(resultado.stdout)

        print(f"\n--- TRACEROUTE {rtr} ---")
        cmd = f"client traceroute -n {rtr}"
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(resultado.stdout)

def test_ICMP_Destination_host_unreachable():
    
    print("\nTest para checkear el msje ICMP 'Destination host unreachable'\n"
    "desde el cliente a una IP inalcanzable.")

    # Apagar server1              
    cmd = "link vhost4 server1 down"
    resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(resultado.stdout)
    print("🔴 Server1 desconectado")

    cmd = f"client ping -c 3 {hosts['servers'][0]}"
    resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(resultado.stdout)

    # Volver a subirlo
    cmd = "link vhost4 server1 up"
    resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(resultado.stdout)
    print("🟢 Server1 reconectado")

def test_ClienteTest():

    print("Ejecutando ClienteTest.py para pruebas de todo tipo para RPC y mas...")

    cmd = "client python3.8 ClienteTest.py"
    resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(resultado.stdout)


def main():
    time.sleep(2)  # Esperar a que la red esté lista
    test_ICMP_ping_traceroute_server()
    test_ICMP_ping_traceroute_router()
    test_ICMP_Destination_host_unreachable()
    test_ClienteTest()



    


