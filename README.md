
Simple IP Router & Cliente-Servidor XML-RPC 

Este repositorio contiene una implementación completa (Full-Stack Networking) que abarca desde la capa de red hasta la capa de aplicación. El proyecto integra un **Enrutador IP programado en C** (con soporte para IP Forwarding, ARP, ICMP y enrutamiento dinámico RIPv2) operando sobre una red SDN simulada en **Mininet**, junto con una arquitectura **Cliente-Servidor XML-RPC en Python** desarrollada desde cero sobre sockets POSIX.



##  Estructura del Repositorio

*   **`Cli-Serv/`** (Capa de Aplicación - XML-RPC)
    *   `client2.py` / `server2.py`: Implementación del protocolo XML-RPC utilizando sockets nativos de Python sobre HTTP (POST).
    *   `tests/`: Batería de pruebas concurrentes, tests de estrés, y scripts auxiliares (`testConcurrencia.py`, simulación de clientes falsos, etc.).
*   **`Router/`** (Capa de Red - Enrutador IP y Entorno SDN)
    *   `enrutamiento/`: Código fuente en C del enrutador virtual. Contiene la lógica central de reenvío IP, caché ARP (`sr_arpcache.c`), tablas estáticas (`sr_rt.c`) y el protocolo RIPv2 (`sr_rip.c`).
    *   `pox/` y `pox_module/`: Controlador SDN utilizado como framework de base.
    *   `pwospf_topo.py`: Topología de Mininet (1 cliente, 2 servidores, 5 routers).
    *   Scripts de despliegue: `run_mininet.sh`, `run_pox.sh`, `run_sr.sh`.

---

##  Funcionalidades Implementadas

### 1. Biblioteca de Procedimientos Remotos (XML-RPC)
Arquitectura cliente-servidor desarrollada desde cero con la API de sockets POSIX de Python.
*   **Cliente:** Captura de parámetros dinámica, serialización (marshalling) a formato XML y transmisión mediante peticiones HTTP POST.
*   **Servidor:** Escucha concurrente, validación de HTTP, parseo de XML (unmarshalling), ejecución de procedimientos remotos y encapsulación de las respuestas.
*   **Gestión de Errores:** Control de faltas (Faults) en tiempo de ejecución por errores de serialización, métodos inexistentes y parámetros inválidos.

### 2. Enrutador IP (IP Forwarding & Routing)
Motor completo de procesamiento de datagramas implementado en C:
*   **Reenvío (Forwarding) y ARP:** Análisis de tramas raw Ethernet, validación de sumas de comprobación IP, alteración de TTL y *Longest Prefix Match*. Resolución y encolamiento de resoluciones físicas usando una tabla temporal (ARP Cache).
*   **Enrutamiento Dinámico (RIPv2):** Implementación del algoritmo vector-distancia para el autodescubrimiento de rutas. Utiliza actualizaciones UDP (puerto 520) dirigidas a la IP multicast `224.0.0.9`. Soporta métricas infinitas y limpieza de rutas inactivas (*timeout* y *garbage-collector*).
*   **Mensajería ICMP:** Generación de notificaciones de error: *Echo Reply*, *Destination Net/Host Unreachable*, *Port Unreachable* y *Time Exceeded*.

---

##  Dependencias y Despliegue

El proyecto está diseñado para ejecutarse en entornos Linux equipados con las siguientes herramientas:
*   **Mininet**: Simulador de topologías de red.
*   **POX**: Plataforma de control SDN basada en Python.
*   **Python 3.x**: Entorno de ejecución para el stack XML-RPC.
*   **Herramientas C (`gcc`, `make`)**: Para la compilación de la lógica del enrutador.

### 1. Compilar el Enrutador
Abre una terminal y compila el código fuente en C:
```bash
cd Router/enrutamiento
make
```

### 2. Iniciar la Infraestructura de Red (SDN & Mininet)
Se recomienda utilizar terminales independientes para cada componente.

*   **Terminal 1 (Controlador POX):**
    ```bash
    cd Router
    ./run_pox.sh
    ```
*   **Terminal 2 (Topología Mininet):**
    Una vez inicializado POX, levanta la red virtual:
    ```bash
    cd Router
    sudo ./run_mininet.sh
    ```

### 3. Ejecutar los Nodos Enrutadores (Simple Router)
Mantén interactiva la consola de Mininet. Abre 5 terminales adicionales (una para cada switch virtual) y conecta la instancia de enrutamiento al controlador:
```bash
cd Router
./run_sr.sh 127.0.0.1 vhost1
# Repite la ejecución para vhost2, vhost3, vhost4 y vhost5
```

### 4. Pruebas Básicas de Red
Desde la línea de comandos de Mininet (`mininet>`), comprueba el estado de los enlaces y la resolución RIP/ARP:
```bash
mininet> client ping -c 3 150.150.0.2
mininet> client traceroute -n 100.100.0.2
```

### 5. Ejecución del Entorno Aplicativo RPC
Con la capa de red estabilizada, inicia el tráfico de aplicación inyectando los scripts Python en los nodos (`server1`, `server2`, `client`):

```bash
mininet> server1 nohup python3 ../Cli-Serv/server2.py &
mininet> server2 nohup python3 ../Cli-Serv/server2.py &
mininet> client python3 ../Cli-Serv/tests/ClienteTest.py
```

### 6. Captura de Tráfico (Wireshark / tcpdump)
Para la depuración del intermedio (mensajes de convergencia RIP o análisis XML), puedes enganchar `tcpdump` a las interfaces virtuales:
```bash
mininet> server1 nohup sudo tcpdump -n -i server1-eth0 -w server1.pcap &
mininet> vhost1 nohup sudo tcpdump -n -i vhost1-eth1 -w vhost1.pcap &
```
Al culminar la experimentación, detén los procesos para escribir correctamente los archivos `.pcap`:
```bash
mininet> server1 killall tcpdump
mininet> vhost1 killall tcpdump
```

---

##  Créditos y Reconocimientos

Este proyecto toma como base bibliotecas de infraestructura y código *stub* académico de código abierto:

*   **Simple Router (SR) / VNS (Virtual Network System):** La arquitectura base en C para el desarrollo del enrutador IP emulado fue concebida originariamente por la **Universidad de Stanford** para su curso *CS144*.
*   **Controlador POX:** Framework OpenFlow / SDN desarrollado por James McCauley ([repositorio](https://github.com/noxrepo/pox)).
*   **Mininet:** Herramienta ágil orientada a la creación de redes de computadoras virtuales realistas.
```
