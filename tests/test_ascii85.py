import unittest
from pdfminer.ascii85 import ascii85decode, asciihexdecode


class TestAscii85(unittest.TestCase):
    def test_ascii85decode(self):
        ascii85_decode = ascii85decode(b'9jqo^BlbD-BleB1DJ+*+F(f,q')
        decode85_ans = b'Man is distinguished'
        self.assertEqual(ascii85_decode, decode85_ans)

        ascii85_decode_2 = ascii85decode(b'E,9)oF*2M7/c~>')
        decode85_ans_2 = b'pleasure.'
        self.assertEqual(ascii85_decode_2, decode85_ans_2)

    def test_asciihexcode(self):
        ascii_hex = asciihexdecode(b'61 62 2e6364   65')
        ascii_hex_ans = b'ab.cde'
        self.assertEqual(ascii_hex, ascii_hex_ans)

        ascii_hex_2 = asciihexdecode(b'61 62 2e6364   657>')
        ascii_hex_ans_2 = b'ab.cdep'
        self.assertEqual(ascii_hex_2, ascii_hex_ans_2)

        ascii_hex_3 = asciihexdecode(b'7>')
        ascii_hex_ans_3 = b'p'
        self.assertEqual(ascii_hex_3, ascii_hex_ans_3)


if __name__ == '__main__':
    unittest.main()
