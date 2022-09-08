import unittest
from pdfminer.runlength import rldecode


class TestRunLength(unittest.TestCase):

    def test_decoding(self):
        s = b'\x05123456\xfa7\x04abcde\x80junk'
        self.assertEqual(rldecode(s), b'1234567777777abcde')
