#!/usr/bin/env python3
"""
Script de automatización para pruebas del Obligatorio 1 - Redes 2025.
Ejecuta los servidores y el cliente dentro de Mininet, y realiza ping y traceroute.
"""

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
import time

def run_network():
    setLogLevel('info')
    info('*** Creando red...\n')
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink)

    # Crear nodos
    info('*** Creando hosts\n')
    client = net.addHost('client', ip='100.0.0.1/24')
    server1 = net.addHost('server1', ip='150.150.0.2/24')
    server2 = net.addHost('server2', ip='100.100.0.2/24')

    info('*** Creando switch\n')
    s1 = net.addSwitch('s1')

    info('*** Creando enlaces\n')
    net.addLink(client, s1)
    net.addLink(server1, s1)
    net.addLink(server2, s1)

    info('*** Iniciando red\n')
    net.start()

    # Esperar a que se configuren las interfaces
    time.sleep(2)

    info('*** Verificando conectividad básica\n')
    net.pingAll()

    info('*** Levantando servidores en segundo plano...\n')
    server1.cmd('nohup python3 Servidor1.py &')
    server2.cmd('nohup python3 Servidor2.py &')

    time.sleep(3)



    info('*** Pruebas de red\n')
    info('Ping del cliente a server1:\n')
    print(client.cmd('ping -c 3 150.150.0.2'))

    info('Ping del cliente a server2:\n')
    print(client.cmd('ping -c 3 100.100.0.2'))

    info('Traceroute del cliente a server1:\n')
    print(client.cmd('traceroute -n 150.150.0.2'))

    info('Traceroute del cliente a server2:\n')
    print(client.cmd('traceroute -n 100.100.0.2'))

    info('*** Fin de las pruebas. Entrando en CLI para debug opcional.\n')
    CLI(net)

    info('*** Deteniendo red\n')
    net.stop()

if __name__ == '__main__':
    run_network()
