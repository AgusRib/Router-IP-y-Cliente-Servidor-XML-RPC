import unittest
import xmlrpc.client
import xmlrpc.server

class TestXMLRPCIntegration(unittest.TestCase):
    def setUp(self):
        # Setup for the test servers
        self.server1 = xmlrpc.server.SimpleXMLRPCServer(('localhost', 8000))
        self.server2 = xmlrpc.server.SimpleXMLRPCServer(('localhost', 8001))

        # Define procedures for server 1
        self.server1.register_function(lambda x, y: x + y, 'add')
        self.server1.register_function(lambda x, y: x - y, 'subtract')
        self.server1.register_function(lambda x, y: x * y, 'multiply')

        # Define procedures for server 2
        self.server2.register_function(lambda x, y: x / y if y != 0 else 'Error', 'divide')
        self.server2.register_function(lambda x: x ** 2, 'square')
        self.server2.register_function(lambda x: x % 2, 'is_even')

        # Start servers in separate threads
        from threading import Thread
        self.server1_thread = Thread(target=self.server1.serve_forever)
        self.server2_thread = Thread(target=self.server2.serve_forever)
        self.server1_thread.start()
        self.server2_thread.start()

    def tearDown(self):
        # Shutdown servers
        self.server1.shutdown()
        self.server2.shutdown()
        self.server1_thread.join()
        self.server2_thread.join()

    def test_server1_add(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8000')
        result = conn.add(5, 3)
        self.assertEqual(result, 8)

    def test_server1_subtract(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8000')
        result = conn.subtract(10, 4)
        self.assertEqual(result, 6)

    def test_server1_multiply(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8000')
        result = conn.multiply(3, 7)
        self.assertEqual(result, 21)

    def test_server2_divide(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8001')
        result = conn.divide(10, 2)
        self.assertEqual(result, 5)

    def test_server2_square(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8001')
        result = conn.square(4)
        self.assertEqual(result, 16)

    def test_server2_is_even(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8001')
        result = conn.is_even(3)
        self.assertEqual(result, 1)  # 1 means odd

    def test_non_existent_method(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8000')
        with self.assertRaises(xmlrpc.client.Fault) as context:
            conn.non_existent_method()
        self.assertEqual(context.exception.faultCode, 2)  # No such method

    def test_error_in_parameters(self):
        conn = xmlrpc.client.ServerProxy('http://localhost:8001')
        with self.assertRaises(xmlrpc.client.Fault) as context:
            conn.divide(10, 0)  # Division by zero
        self.assertEqual(context.exception.faultString, 'Error')

if __name__ == '__main__':
    unittest.main()