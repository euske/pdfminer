import unittest
from tools.latin2ascii import main


class TestLatin2Ascii(unittest.TestCase):
    def test_main(self):
        filename = './samples/simple1.pdf'
        argv = ['latin2ascii.py', filename]
        _, latin2ascii_lines = main(argv)
        with open(filename, 'r') as f:
            lines = bytes(f.read(), 'utf-8')
            self.assertEqual(latin2ascii_lines, lines)


if __name__ == '__main__':
    unittest.main()
