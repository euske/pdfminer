import unittest

from pdfminer.arcfour import Arcfour


class TestArcfour(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(Arcfour(b'Key').process(b'Plaintext').encode('hex'),
                         'bbf316e8d940af0ad3')

        self.assertEqual(Arcfour(b'Wiki').process(b'pedia').encode('hex'),
                         '1021bf0420')

        self.assertEqual(Arcfour(b'Secret').process(b'Attack at dawn').encode('hex'),
                         '45a01f645fc35b383552544b9bf5')
