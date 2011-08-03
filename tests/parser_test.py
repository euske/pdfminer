import io

from pdfminer.psparser import PSBaseParser, PSStackParser, KWD, LIT, PSEOF
from .util import eq_

TESTDATA = br'''%!PS
begin end
 "  @ #
/a/BCD /Some_Name /foo#5f#xbaa
0 +1 -2 .5 1.234
(abc) () (abc ( def ) ghi)
(def\040\0\0404ghi) (bach\\slask) (foo\nbaa)
(this % is not a comment.)
(foo
baa)
(foo\
baa)
<> <20> < 40 4020 >
<abcd00
12345>
func/a/b{(c)do*}def
[ 1 (z) ! ]
<< /foo (bar) >>
'''

def get_tokens(s):
    class MyParser(PSBaseParser):
        def flush(self):
            self.add_results(*self.popall())
    parser = MyParser(io.BytesIO(s))
    r = []
    try:
        while True:
            r.append(parser.nexttoken())
    except PSEOF:
        pass
    return r

def get_objects(s):
    class MyParser(PSStackParser):
        def flush(self):
            self.add_results(*self.popall())
    parser = MyParser(io.BytesIO(s))
    r = []
    try:
        while True:
            r.append(parser.nextobject())
    except PSEOF:
        pass
    return r

def withoutpos(tokens):
    return [token for pos, token in tokens]

def test_tokens():
    EXPECTED = [
        (5, KWD('begin')), (11, KWD('end')), (16, KWD('"')), (19, KWD('@')),
        (21, KWD('#')), (23, LIT('a')), (25, LIT('BCD')), (30, LIT('Some_Name')),
        (41, LIT('foo_xbaa')), (54, 0), (56, 1), (59, -2), (62, 0.5),
        (65, 1.234), (71, 'abc'), (77, ''), (80, 'abc ( def ) ghi'),
        (98, 'def \x00 4ghi'), (118, 'bach\\slask'), (132, 'foo\nbaa'),
        (143, 'this % is not a comment.'), (170, 'foo\nbaa'), (180, 'foobaa'),
        (191, ''), (194, ' '), (199, '@@ '), (211, b'\xab\xcd\x00\x124\x05'),
        (226, KWD('func')), (230, LIT('a')), (232, LIT('b')),
        (234, KWD('{')), (235, 'c'), (238, KWD('do*')), (241, KWD('}')),
        (242, KWD('def')), (246, KWD('[')), (248, 1), (250, 'z'), (254, KWD('!')),
        (256, KWD(']')), (258, KWD('<<')), (261, LIT('foo')), (266, 'bar'),
        (272, KWD('>>'))
    ]
    tokens = get_tokens(TESTDATA)
    eq_(tokens, EXPECTED)

def test_objects():
    EXPECTED = [
        (23, LIT('a')), (25, LIT('BCD')), (30, LIT('Some_Name')),
        (41, LIT('foo_xbaa')), (54, 0), (56, 1), (59, -2), (62, 0.5),
        (65, 1.234), (71, 'abc'), (77, ''), (80, 'abc ( def ) ghi'),
        (98, 'def \x00 4ghi'), (118, 'bach\\slask'), (132, 'foo\nbaa'),
        (143, 'this % is not a comment.'), (170, 'foo\nbaa'), (180, 'foobaa'),
        (191, ''), (194, ' '), (199, '@@ '), (211, b'\xab\xcd\x00\x124\x05'),
        (230, LIT('a')), (232, LIT('b')), (234, ['c']), (246, [1, 'z']),
        (258, {'foo': 'bar'}),
    ]
     
    objs = get_objects(TESTDATA)
    eq_(objs, EXPECTED)

def test_byte_strings_are_parsed_as_bytes():
    # Normally, all strings in PS are ascii, but sometimes you get byte strings for stuff like
    # encryption. These strings will be parsed as bytes.
    TESTDATA = b"""%PDF-1.4
(\xfe\xff)<feff>
"""
    tokens = get_tokens(TESTDATA)
    eq_(len(tokens), 2)
    eq_(tokens[0][1], b'\xfe\xff')
    eq_(tokens[1][1], b'\xfe\xff')

def test_detect_escaped_parens_in_string():
    # escaped parens in strings are correctly detected and not counted in the parens balancing thing.
    s = br'(str1\(foo)(str2)'
    tokens = get_tokens(s)
    EXPECTED = ['str1(foo', 'str2']
    eq_(withoutpos(tokens), EXPECTED)

def test_true_false_keywords_translate_to_bool():
    s = br'true false'
    tokens = get_tokens(s)
    EXPECTED = [True, False]
    eq_(withoutpos(tokens), EXPECTED)

def test_hexstring_without_delimiter():
    # hexstrings don't need to end with a delimiter
    s = b"<0042>foo"
    tokens = get_tokens(s)
    EXPECTED = ['\x00\x42', KWD('foo')]
    eq_(withoutpos(tokens), EXPECTED)

def test_octal_string_over_byte_value():
    # when we have what looks like an octal escape char with a value that's over 255, we don't parse
    # it as octal because if we do we end up with an encoding error later.
    s = b"(\\500)"
    tokens = get_tokens(s)
    EXPECTED = ['\\500']
    eq_(withoutpos(tokens), EXPECTED)
