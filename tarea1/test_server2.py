import unittest
from xmlrpc import ServerProxy

class TestServer2(unittest.TestCase):

    def setUp(self):
        self.server_url = 'http://localhost:8001'  # Adjust the port as needed
        self.proxy = ServerProxy(self.server_url)

    def test_procedure1(self):
        result = self.proxy.procedure1(1, 2)
        self.assertEqual(result, 3)  # Assuming procedure1 adds two numbers

    def test_procedure2(self):
        result = self.proxy.procedure2('Hello', 'World')
        self.assertEqual(result, 'Hello World')  # Assuming procedure2 concatenates strings

    def test_procedure3(self):
        result = self.proxy.procedure3(5)
        self.assertEqual(result, 25)  # Assuming procedure3 squares the number

    def test_non_existent_procedure(self):
        with self.assertRaises(Exception):
            self.proxy.non_existent_procedure()

    def test_invalid_parameters(self):
        with self.assertRaises(Exception):
            self.proxy.procedure1('invalid', 2)  # Assuming procedure1 expects integers

if __name__ == '__main__':
    unittest.main()