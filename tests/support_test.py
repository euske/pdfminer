# test for support units around pdfminer

from pytest import raises

from pdfminer import arcfour, ascii85, lzw, rijndael, runlength, utils
from .util import eq_

def test_arcfour():
    eq_(arcfour.Arcfour(b'Key').process(b'Plaintext'), bytes.fromhex('bbf316e8d940af0ad3'))
    eq_(arcfour.Arcfour(b'Wiki').process(b'pedia'), bytes.fromhex('1021bf0420'))
    eq_(arcfour.Arcfour(b'Secret').process(b'Attack at dawn'), bytes.fromhex('45a01f645fc35b383552544b9bf5'))

def test_ascii85decode():
    eq_(ascii85.ascii85decode('9jqo^BlbD-BleB1DJ+*+F(f,q'), b'Man is distinguished')
    eq_(ascii85.ascii85decode('E,9)oF*2M7/c~>'), b'pleasure.')

def test_asciihexdecode():
    eq_(ascii85.asciihexdecode('61 62 2e6364   65'), 'ab.cde')
    eq_(ascii85.asciihexdecode('61 62 2e6364   657>'), 'ab.cdep')
    eq_(ascii85.asciihexdecode('7>'), 'p')

def test_lzwdecode():
    eq_(lzw.lzwdecode(b'\x80\x0b\x60\x50\x22\x0c\x0c\x85\x01'), b'\x2d\x2d\x2d\x2d\x2d\x41\x2d\x2d\x2d\x42')

def test_lzwdecode_garbage():
    # Sometimes, there's garbage at the end of the data like space characters and newline. If a code
    # can't be found in the table, don't raise an Index error, but just return what has been decoded
    # yet.
    eq_(lzw.lzwdecode(b'\x80\x0b\x60\x50\x22\x0c\x0c\x85\x01\xff\xff'), b'\x2d\x2d\x2d\x2d\x2d\x41\x2d\x2d\x2d\x42')

def test_lzwdecode_invalid():
    # Sometimes, the data is simply invalid, which leads us to try to read the character table when
    # there's none. Just return nothing.
    eq_(lzw.lzwdecode(b'\x80\x80\r\n'), b'')

def test_RijndaelDecryptor():
    key = bytes.fromhex('00010203050607080a0b0c0d0f101112')
    ciphertext = bytes.fromhex('d8f532538289ef7d06b506a4fd5be9c9')
    plaintext = bytes.fromhex('506812a45f08c889b97f5980038b8359')
    eq_(rijndael.RijndaelDecryptor(key, 128).decrypt(ciphertext), plaintext)

def test_RijndaelEncryptor():
    key = bytes.fromhex('00010203050607080a0b0c0d0f101112')
    ciphertext = bytes.fromhex('d8f532538289ef7d06b506a4fd5be9c9')
    plaintext = bytes.fromhex('506812a45f08c889b97f5980038b8359')
    eq_(rijndael.RijndaelEncryptor(key, 128).encrypt(plaintext), ciphertext)

def test_rldecode():
    s = "\x05123456\xfa7\x04abcde\x80junk"
    eq_(runlength.rldecode(s), '1234567777777abcde')

def test_nunpack():
    eq_(utils.nunpack(b'\x42'), 0x42)
    eq_(utils.nunpack(b'\x41\x42'), 0x4142)
    eq_(utils.nunpack(b'\x40\x41\x42'), 0x404142)
    eq_(utils.nunpack(b'\x39\x40\x41\x42'), 0x39404142)
    eq_(utils.nunpack(b'', default=42), 42)
    with raises(TypeError):
        utils.nunpack(b'\x42\x42\x42\x42\x42')
    # strings are correctly converted to bytes
    eq_(utils.nunpack('\x42\xfc'), 0x42fc)

def test_trailiter():
    eq_(list(utils.trailiter([])), [])
    eq_(list(utils.trailiter(['foo'])), [(None, 'foo')])
    eq_(list(utils.trailiter(['foo', 'bar'])), [(None, 'foo'), ('foo', 'bar')])
    eq_(list(utils.trailiter(['foo', 'bar'], skipfirst=True)), [('foo', 'bar')])
    eq_(list(utils.trailiter([], skipfirst=True)), []) # no crash
