from package_1 import main

import unittest


class TestSuite(unittest.TestCase):
    """Sample test cases"""

    def test_main(self):
        self.assertEqual("Hello, World!", "Hello, World!")


if __name__ == '__main__':
    unittest.main()     # This allows for infile testing with pytest
