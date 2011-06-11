#!/usr/bin/env python2.7

""" Python implementation of Arcfour encryption algorithm.

This code is in the public domain.

"""

from __future__ import unicode_literals

class Arcfour(object):
    def __init__(self, key):
        s = range(256)
        j = 0
        klen = len(key)
        for i in xrange(256):
            j = (j + s[i] + ord(key[i % klen])) % 256
            (s[i], s[j]) = (s[j], s[i])
        self.s = s
        (self.i, self.j) = (0, 0)
        return

    def process(self, data):
        (i, j) = (self.i, self.j)
        s = self.s
        r = b''
        for c in data:
            i = (i+1) % 256
            j = (j+s[i]) % 256
            (s[i], s[j]) = (s[j], s[i])
            k = s[(s[i]+s[j]) % 256]
            r += chr(ord(c) ^ k)
        (self.i, self.j) = (i, j)
        return r

def test():
    assert Arcfour(b'Key').process(b'Plaintext').encode('hex') == 'bbf316e8d940af0ad3'
    assert Arcfour(b'Wiki').process(b'pedia').encode('hex') == '1021bf0420'
    assert Arcfour(b'Secret').process(b'Attack at dawn').encode('hex') == '45a01f645fc35b383552544b9bf5'

if __name__ == '__main__':
    test()
