import unittest
from pdfminer.ascii85 import ascii85decode, asciihexdecode


class TestAscii85Decode(unittest.TestCase):
    def test_ascii85(self):
        decoded_value = ascii85decode(b'9jqo^BlbD-BleB1DJ+*+F(f,q')
        self.assertEqual(decoded_value, b'Man is distinguished')

    def test_ascii85_with_adobe_encoding(self):
        decoded_value = ascii85decode(b'E,9)oF*2M7/c~>')
        self.assertEqual(decoded_value, b'pleasure.')

        ascii85_decode_3 = ascii85decode(b'9jqo^z')
        decode85_ans_3 = b'Man \x00\x00\x00\x00'
        self.assertEqual(ascii85_decode_3, decode85_ans_3)

        ascii85_decode_4 = ascii85decode(b'9jqo^~>')
        decode85_ans_4 = b'Man '
        self.assertEqual(ascii85_decode_4, decode85_ans_4)


class TestAsciiHexDecode(unittest.TestCase):
    def test_decode_1(self):
        decoded_value = asciihexdecode(b'61 62 2e6364   65')
        self.assertEqual(decoded_value, b'ab.cde')

    def test_decode_2(self):
        decoded_value = asciihexdecode(b'61 62 2e6364   657>')
        self.assertEqual(decoded_value, b'ab.cdep')

    def test_decode_3(self):
        decoded_value = asciihexdecode(b'7>')
        self.assertEqual(decoded_value, b'p')
