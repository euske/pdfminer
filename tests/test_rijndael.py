import unittest
from pdfminer.rijndael import RijndaelEncryptor, RijndaelDecryptor


class TestRijndael(unittest.TestCase):
    def test_encryptor(self):
        key = bytes.fromhex('00010203050607080a0b0c0d0f101112')
        plaintext = bytes.fromhex('506812a45f08c889b97f5980038b8359')
        expected = 'd8f532538289ef7d06b506a4fd5be9c9'

        self.assertEqual(RijndaelEncryptor(key, 128).encrypt(plaintext).hex(),
                         expected)

    def test_decryptor(self):
        key = bytes.fromhex('00010203050607080a0b0c0d0f101112')
        ciphertext = bytes.fromhex('d8f532538289ef7d06b506a4fd5be9c9')
        expected = '506812a45f08c889b97f5980038b8359'

        self.assertEqual(RijndaelDecryptor(key, 128).decrypt(ciphertext).hex(),
                         expected)


if __name__ == '__main__':
    unittest.main()
