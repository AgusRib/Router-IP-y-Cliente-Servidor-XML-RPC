

#!/usr/bin/env python3
"""
Test script para verificar funcionalidad ICMP desde el cliente Mininet.

Para ejecutarlo desde Mininet:

1. Inicia la topología:
   sudo python pwospf_topo.py

2. Desde el CLI de Mininet, ejecuta:
   client python3.8 test/Test_desde_RED.py

Este script se ejecuta directamente en el host 'client' de Mininet.
"""

import subprocess
import time
import sys

# Configuración de hosts y direcciones IP
servers = ["150.150.0.2", "100.100.0.2"]
routers = ["100.0.0.50", "200.200.0.1"]

def run_command(command, description=""):
    """Ejecuta un comando del sistema y muestra los resultados"""
    if description:
        print(f"\n--- {description} ---")
    
    print(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.stdout.strip():
            print("Resultado:")
            print(result.stdout)
        
        if result.stderr.strip():
            print("Errores:")
            print(result.stderr)
            
        if result.returncode != 0:
            print(f"Comando terminó con código de retorno: {result.returncode}")
        
        return result
        
    except subprocess.TimeoutExpired:
        print("⚠️  Comando agotó el tiempo de espera (30s)")
        return None
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return None

def print_separator(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_ICMP_ping_traceroute_server():
    print_separator("TEST ICMP PING/TRACEROUTE A SERVIDORES")
    print("Test para checkear los msjes ICMP 'Time exceeded', 'Echo request' y 'Echo reply'")
    print("mediante traceroute y ping, respectivamente, desde el cliente a los servidores.")

    for srv in servers:
        run_command(f"ping -c 3 {srv}", f"PING {srv}")
        run_command(f"traceroute -n {srv}", f"TRACEROUTE {srv}")

def test_ICMP_ping_traceroute_router():
    print_separator("TEST ICMP PING/TRACEROUTE A ROUTERS")
    print("Test para checkear los msjes ICMP 'Time exceeded', 'Echo request' y 'Echo reply'")
    print("mediante traceroute y ping, respectivamente, desde el cliente al router.")

    for rtr in routers:
        run_command(f"ping -c 3 {rtr}", f"PING {rtr}")
        run_command(f"traceroute -n {rtr}", f"TRACEROUTE {rtr}")

def test_ICMP_Destination_host_unreachable():
    print_separator("TEST ICMP DESTINATION HOST UNREACHABLE")
    print("Test para checkear el msje ICMP 'Destination host unreachable'")
    print("desde el cliente a una IP inalcanzable.")

    # Hacer ping a una IP que debería ser inalcanzable
    unreachable_ip = "192.168.99.99"  # IP que no existe en la topología
    
    print(f"\n🔍 Haciendo ping a IP inexistente: {unreachable_ip}")
    run_command(f"ping -c 5 -W 2 {unreachable_ip}", f"PING a IP inalcanzable {unreachable_ip}")
    
    # También probar con una IP en una red diferente
    unreachable_ip2 = "10.10.10.10"
    print(f"\n🔍 Haciendo ping a otra IP inexistente: {unreachable_ip2}")
    run_command(f"ping -c 3 -W 2 {unreachable_ip2}", f"PING a IP inalcanzable {unreachable_ip2}")
    
    # Probar traceroute a IP inalcanzable
    run_command(f"traceroute -n -w 2 {unreachable_ip}", f"TRACEROUTE a IP inalcanzable {unreachable_ip}")

def test_ClienteTest():
    print_separator("TEST CLIENTE RPC")
    print("Ejecutando ClienteTest.py para pruebas de todo tipo para RPC y mas...")

    # Ejecutar el script de ClienteTest
    run_command("python3 ClienteTest.py", "Ejecutando ClienteTest.py")


def main():
    print_separator("INICIANDO TESTS DE RED DESDE CLIENTE MININET")
    
    print("🖥️  Ejecutándose en el host 'client' de Mininet")
    print("📍 Directorio actual:", subprocess.run("pwd", shell=True, capture_output=True, text=True).stdout.strip())
    
    try:
        # Verificar conectividad básica
        print("\n🔍 Verificando configuración de red del cliente...")
        run_command("ip addr show", "Configuración de interfaces de red")
        run_command("ip route", "Tabla de rutas")
        
        # Ejecutar tests
        test_ICMP_ping_traceroute_server()
        test_ICMP_ping_traceroute_router()  
        test_ICMP_Destination_host_unreachable()
        test_ClienteTest()
        
        print_separator("TESTS COMPLETADOS")
        print("✅ Todos los tests han sido ejecutados correctamente desde el cliente Mininet.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrumpidos por el usuario.")
    except Exception as e:
        print(f"\n❌ Error durante la ejecución de los tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

    


