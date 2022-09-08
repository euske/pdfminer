import unittest
from pdfminer.lzw import lzwdecode


class TestLzwMethods(unittest.TestCase):
    def test1(self):
        obj = lzwdecode(bytes.fromhex('800b6050220c0c8501'))
        self.assertEqual(obj ,b'-----A---B')


if __name__ == '__main__':
    unittest.main()