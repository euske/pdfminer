import unittest

from pdfminer.rijndael import RijndaelDecryptor, RijndaelEncryptor


class TestArcfour(unittest.TestCase):

    def test_example(self):
        key = b'00010203050607080a0b0c0d0f101112'.decode('hex')
        cipher_text = b'd8f532538289ef7d06b506a4fd5be9c9'
        decoded_cipher_text = cipher_text.decode('hex')
        plain_text = '506812a45f08c889b97f5980038b8359'
        decoded_plain_text = plain_text.decode('hex')

        self.assertEqual(RijndaelDecryptor(key, 128).decrypt(decoded_cipher_text),
                         decoded_plain_text)

        self.assertEqual(RijndaelEncryptor(key, 128).encrypt(decoded_plain_text),
                         decoded_cipher_text)
