import unittest

from pdfminer.lzw import lzwdecode


class TestASCIIHEX(unittest.TestCase):

    def test_simple(self):
        # Samples taken from http://en.wikipedia.org/w/index.php?title=Ascii85
        self.assertEqual(lzwdecode(b'\x80\x0b\x60\x50\x22\x0c\x0c\x85\x01'),
                         '\x2d\x2d\x2d\x2d\x2d\x41\x2d\x2d\x2d\x42')
