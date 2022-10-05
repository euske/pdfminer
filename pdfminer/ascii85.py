#!/usr/bin/env python

""" Python implementation of ASCII85/ASCIIHex decoder (Adobe version).

This code is in the public domain.

"""
import re
import base64


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
    # Some ascii85 strings found in pdfs can be encoded as
    # a normal ascii85 string and some with adobe's version
    # of ascii85. The difference with adobe is that it allows
    # a string to start with <~ and end with ~>. We first try
    # decoding the string with the adobe version of ascii85.
    # If that fails, we try decoding it as a normal ascii85 string.
    try:
        return base64.a85decode(data, adobe=True)
    except ValueError:
        return base64.a85decode(data)


# Every pair of hexadecimal characters (a-f, A-F, 0-9)
hex_re = re.compile(r'([a-f\d]{2})', re.IGNORECASE)
# If the number of hexadecimal characters is an odd number, the regex finds the
# last hexadecimal character that does not belong to a pair. This character
# can be followed by zero or more > (whitespace between the brackets is
# allowed)
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

    data = data.decode('latin1')
    # Convert pairs of hexadecimal to decimal
    decimal_values = [int(hx, base=16) for hx in hex_re.findall(data)]

    # Find if the last character has no hexadecimal pair
    pairless_character = trail_re.search(data)
    if pairless_character:
        # Group 1 contains the pairless character. Group 0 would pick the
        # entire matched string.
        character = pairless_character.group(1) + '0'
        decimal_values.append(int(character, base=16))
    return bytes(decimal_values)
