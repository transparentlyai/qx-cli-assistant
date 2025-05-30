import unittest
# Assuming hello_world.py is in the same directory (tmp) or PYTHONPATH is set up
# so that 'hello_world' can be imported.
# If running 'python tmp/test_hello_world.py' from the project root,
# Python adds 'tmp/' to sys.path, so this import should work.
from hello_world import get_greeting

class TestHelloWorld(unittest.TestCase):

    def test_get_greeting(self):
        self.assertEqual(get_greeting(), "Hello, World!")

if __name__ == '__main__':
    unittest.main()
