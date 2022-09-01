import unittest
from pdfminer.runlength import rldecode


class TestArcFourMethods(unittest.TestCase):
    def test_encryptor(self):
        string = b'\x05123456\xfa7\x04abcde\x80junk'
        expected = b'1234567777777abcde'

        self.assertEqual(rldecode(string), expected)


if __name__ == '__main__':
    unittest.main()
