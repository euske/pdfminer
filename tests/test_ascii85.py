import unittest

from pdfminer.ascii85 import ascii85decode, asciihexdecode


class TestASCII85(unittest.TestCase):

    def test_simple(self):
        # Samples taken from http://en.wikipedia.org/w/index.php?title=Ascii85
        self.assertEqual(ascii85decode(b'9jqo^BlbD-BleB1DJ+*+F(f,q'),
                         'Man is distinguished')

        self.assertEqual(ascii85decode(b'E,9)oF*2M7/c~>'),
                         'pleasure.')


class TestASCIIHEX(unittest.TestCase):

    def test_simple(self):
        # Samples taken from http://en.wikipedia.org/w/index.php?title=Ascii85
        self.assertEqual(asciihexdecode(b'61 62 2e6364   65'), 'ab.cde')

        self.assertEqual(asciihexdecode(b'61 62 2e6364   657>'), 'ab.cdep')

        self.assertEqual(asciihexdecode(b'7>'), 'p')
