import unittest
from xmlrpc_redes.src.client import Client

class TestClient(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def test_connect(self):
        conn = self.client.connect('localhost', 8000)
        self.assertIsNotNone(conn)

    def test_remote_procedure_call(self):
        conn = self.client.connect('localhost', 8000)
        result = conn.add(5, 10)  # Assuming 'add' is a method on the server
        self.assertEqual(result, 15)

    def test_non_existent_method(self):
        conn = self.client.connect('localhost', 8000)
        with self.assertRaises(Exception) as context:
            conn.non_existent_method()
        self.assertIn('Method not found', str(context.exception))

    def test_invalid_parameters(self):
        conn = self.client.connect('localhost', 8000)
        with self.assertRaises(Exception) as context:
            conn.add('five', 10)  # Invalid parameter type
        self.assertIn('Invalid parameters', str(context.exception))

if __name__ == '__main__':
    unittest.main()