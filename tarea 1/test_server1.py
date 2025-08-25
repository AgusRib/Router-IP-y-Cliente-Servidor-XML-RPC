import unittest
from xmlrpc import ServerProxy

class TestServer1(unittest.TestCase):
    def setUp(self):
        self.server_url = 'http://localhost:8000'  # Adjust the URL and port as needed
        self.proxy = ServerProxy(self.server_url)

    def test_add_method(self):
        # Assuming there's an add method on the server
        result = self.proxy.add(2, 3)
        self.assertEqual(result, 5)

    def test_subtract_method(self):
        # Assuming there's a subtract method on the server
        result = self.proxy.subtract(5, 3)
        self.assertEqual(result, 2)

    def test_non_existent_method(self):
        with self.assertRaises(Exception) as context:
            self.proxy.non_existent_method()
        self.assertIn('method not found', str(context.exception))

    def test_invalid_parameters(self):
        with self.assertRaises(Exception) as context:
            self.proxy.add('two', 3)  # Invalid parameter type
        self.assertIn('invalid parameters', str(context.exception))

if __name__ == '__main__':
    unittest.main()