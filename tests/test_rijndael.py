import unittest
from pdfminer.rijndael import *


class MyTestCase(unittest.TestCase):
    # test for the decryption function

    def test_1(self):
        key = bytes.fromhex('00010203050607080a0b0c0d0f101112')
        ciphertext = bytes.fromhex('d8f532538289ef7d06b506a4fd5be9c9')
        k_1 = RijndaelDecryptor(key, 128).decrypt(ciphertext).hex()
        self.assertEqual(k_1, '506812a45f08c889b97f5980038b8359')

    # test for the encryption function

    def test_2(self):
        key = bytes.fromhex('00010203050607080a0b0c0d0f101112')
        plaintext = bytes.fromhex('506812a45f08c889b97f5980038b8359')
        k_2 = RijndaelEncryptor(key, 128).encrypt(plaintext).hex()
        self.assertEqual(k_2, 'd8f532538289ef7d06b506a4fd5be9c9')


if __name__ == '__main__':
    unittest.main()
