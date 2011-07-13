#!/usr/bin/env python3

""" Python implementation of ASCII85/ASCIIHex decoder (Adobe version).

This code is in the public domain.

"""

import re
import struct

def ascii85decode(data):
    """
    In ASCII85 encoding, every four bytes are encoded with five ASCII
    letters, using 85 different types of characters (as 256**4 < 85**5).
    When the length of the original bytes is not a multiple of 4, a special
    rule is used for round up.
    
    The Adobe's ASCII85 implementation is slightly different from
    its original in handling the last characters.
    
    The sample string is taken from:
      http://en.wikipedia.org/w/index.php?title=Ascii85
    """
    if isinstance(data, str):
        data = data.encode('ascii')
    n = b = 0
    out = bytearray()
    for c in data:
        if ord('!') <= c and c <= ord('u'):
            n += 1
            b = b*85+(c-33)
            if n == 5:
                out += struct.pack(b'>L',b)
                n = b = 0
        elif c == ord('z'):
            assert n == 0
            out += b'\0\0\0\0'
        elif c == ord('~'):
            if n:
                for _ in range(5-n):
                    b = b*85+84
                out += struct.pack(b'>L',b)[:n-1]
            break
    return bytes(out)

hex_re = re.compile(r'([a-f\d]{2})', re.IGNORECASE)
trail_re = re.compile(r'^(?:[a-f\d]{2}|\s)*([a-f\d])[\s>]*$', re.IGNORECASE)
def asciihexdecode(data):
    """
    ASCIIHexDecode filter: PDFReference v1.4 section 3.3.1
    For each pair of ASCII hexadecimal digits (0-9 and A-F or a-f), the
    ASCIIHexDecode filter produces one byte of binary data. All white-space
    characters are ignored. A right angle bracket character (>) indicates
    EOD. Any other characters will cause an error. If the filter encounters
    the EOD marker after reading an odd number of hexadecimal digits, it
    will behave as if a 0 followed the last digit.
    """
    decode = (lambda hx: chr(int(hx, 16)))
    out = list(map(decode, hex_re.findall(data)))
    m = trail_re.search(data)
    if m:
        out.append(decode("%c0" % m.group(1)))
    return ''.join(out)
