import unittest
from pdfminer.arcfour import Arcfour


class TestArcFourMethods(unittest.TestCase):
	def test_short_string(self):
		key = b'Wiki'
		text = b'pedia'
		expected = '1021bf0420'

		self.assertEqual(Arcfour(key).process(text).hex(), expected)

	def test_medium_string(self):
		key = b'Key'
		text = b'Plaintext'
		expected = 'bbf316e8d940af0ad3'

		self.assertEqual(Arcfour(key).process(text).hex(), expected)

	def test_long_string(self):
		key = b'Secret'
		text = b'Attack at dawn'
		expected = '45a01f645fc35b383552544b9bf5'

		self.assertEqual(Arcfour(key).process(text).hex(), expected)


if __name__ == '__main__':
	unittest.main()
