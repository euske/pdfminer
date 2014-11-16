import unittest

from pdfminer.runlength import rldecode


class TestASCIIHEX(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(rldecode(b'\x05123456\xfa7\x04abcde\x80junk'),
                         '1234567777777abcde')
