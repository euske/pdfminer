import unittest
from pdfminer.arcfour import Arcfour

class TestArcfourMethods(unittest.TestCase):
    def test_1(self):
        arcfour = Arcfour(b'Key').process(b'Plaintext').hex()
        self.assertEqual(arcfour, 'bbf316e8d940af0ad3')
    def test_2(self):
        arcfour = Arcfour(b'Wiki').process(b'pedia').hex()
        self.assertEqual(arcfour, '1021bf0420')
    def test_3(self):
        arcfour = Arcfour(b'Secret').process(b'Attack at dawn').hex()
        self.assertEqual(arcfour, '45a01f645fc35b383552544b9bf5')
        

if __name__ == '__main__':
    unittest.main()


    