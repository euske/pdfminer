import unittest
from pdfminer.ascii85 import ascii85decode, asciihexdecode


class TestAsciiDecode(unittest.TestCase):

		def test_ascii85_decode_short(self):
				string_to_decode = b'E,9)oF*2M7/c~>'
				expected = b'pleasure.'

				self.assertEqual(ascii85decode(string_to_decode), expected)

		def test_ascii85_decode_long(self):
				string_to_decode = b'9jqo^BlbD-BleB1DJ+*+F(f,q'
				expected = b'Man is distinguished'

				self.assertEqual(ascii85decode(string_to_decode), expected)

		def test_asciihex_decode_short(self):
				string_to_decode = b'7>'
				expected = b'p'

				self.assertEqual(asciihexdecode(string_to_decode), expected)

		def test_asciihex_decode_medium(self):
				string_to_decode = b'61 62 2e6364   65'
				expected = b'ab.cde'

				self.assertEqual(asciihexdecode(string_to_decode), expected)

		def test_asciihex_decode_long(self):
				string_to_decode = b'61 62 2e6364   657>'
				expected = b'ab.cdep'

				self.assertEqual(asciihexdecode(string_to_decode), expected)


if __name__ == '__main__':
		unittest.main()
