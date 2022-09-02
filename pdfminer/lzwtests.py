import unittest2
from lzw import lzwdecode

class TestLzwMethods(unittest2.TestCase):
    def test1(self):
        obj = lzwdecode(bytes.fromhex('800b6050220c0c8501'))
        self.assertEqual(obj ,b'-----A---B')


if __name__ == '__main__':
    unittest2.main()



"""
    >>> lzwdecode(bytes.fromhex('800b6050220c0c8501'))
    b'-----A---B'
    """