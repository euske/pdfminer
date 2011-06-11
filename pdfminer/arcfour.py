#!/usr/bin/env python3

""" Python implementation of Arcfour encryption algorithm.

This code is in the public domain.

"""

class Arcfour(object):
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

def test():
    assert Arcfour(b'Key').process(b'Plaintext') == bytes.fromhex('bbf316e8d940af0ad3')
    assert Arcfour(b'Wiki').process(b'pedia') == bytes.fromhex('1021bf0420')
    assert Arcfour(b'Secret').process(b'Attack at dawn') == bytes.fromhex('45a01f645fc35b383552544b9bf5')

if __name__ == '__main__':
    test()
