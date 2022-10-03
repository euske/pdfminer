#!/usr/bin/env python

""" Python implementation of Arcfour encryption algorithm.

This code is in the public domain.

"""


#  Arcfour
#
class Arcfour:

    """
    >>> Arcfour(b'Key').process(b'Plaintext').hex()
    'bbf316e8d940af0ad3'
    >>> Arcfour(b'Wiki').process(b'pedia').hex()
    '1021bf0420'
    >>> Arcfour(b'Secret').process(b'Attack at dawn').hex()
    '45a01f645fc35b383552544b9bf5'
    """

    def __init__(self, key):
        s = list(range(256))
        j = 0
        klen = len(key)
        for i in range(256):
            j = (j + s[i] + key[i % klen]) % 256
            (s[i], s[j]) = (s[j], s[i])
        self.s = s
        (self.i, self.j) = (0, 0)
        return

    def process(self, data):
        (i, j) = (self.i, self.j)
        s = self.s
        r = []
        for c in data:
            i = (i+1) % 256
            j = (j+s[i]) % 256
            (s[i], s[j]) = (s[j], s[i])
            k = s[(s[i]+s[j]) % 256]
            r.append(c ^ k)
        (self.i, self.j) = (i, j)
        return bytes(r)

    encrypt = decrypt = process


new = Arcfour

# test
if __name__ == '__main__':
    import doctest
    print('pdfminer.arcfour:', doctest.testmod())
