from client2 import Client
import threading
import time

def client_thread(thread_id):
    """Función que ejecuta cada cliente en su propio thread"""
    try:
        client = Client()
        client.connect("127.0.0.1", 12000)
        time.sleep(1) 
        
        # Cada thread hace diferentes llamadas para testear concurrencia
        if thread_id % 3 == 0:
            result = client.suma(thread_id, 10)
            print(f"Thread {thread_id}: suma({thread_id}, 10) = {result}")
        elif thread_id % 3 == 1:
            result = client.multiplicar(thread_id, 5)
            print(f"Thread {thread_id}: multiplicar({thread_id}, 5) = {result}")
        else:
            result = client.ordenar([thread_id, 1, 5, 2])
            print(f"Thread {thread_id}: ordenar([{thread_id}, 1, 5, 2]) = {result}")
        
    except Exception as e:
        print(f"Thread {thread_id} error: {e}")

def test_concurrencia(num_clients=10):
    """Test de concurrencia con múltiples clientes simultáneos"""
    print(f"\nIniciando test de concurrencia con {num_clients} clientes...")
    
    
    # Crear threads de clientes
    threads = []
    for i in range(num_clients):
        t = threading.Thread(target=client_thread, args=(i,))
        threads.append(t)
    
    # Iniciar todos los threads
    start_time = time.time()
    for t in threads:
        t.start()
         # Pequeña pausa entre inicio de clientes
    
    # Esperar a que todos terminen
    for t in threads:
        t.join()
    
    elapsed_time = time.time() - start_time
    
    print(f"Test completado en {elapsed_time:.2f} segundos")

if __name__ == "__main__":
    test_concurrencia(50)  # Probar con 10 clientes concurrentes