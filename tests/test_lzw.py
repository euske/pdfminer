import unittest
from pdfminer.lzw import lzwdecode


class TestLZW(unittest.TestCase):
    def test_lzwdecode(self):
        string_to_decode = "800b6050220c0c8501"
        expected = b"-----A---B"

        self.assertEqual(lzwdecode(bytes.fromhex(string_to_decode)), expected)


if __name__ == "__main__":
    unittest.main()
