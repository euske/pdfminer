import sys
import re
from .utils import choplist
from . import pslexer

STRICT = 0


##  PS Exceptions
##
class PSException(Exception): pass
class PSEOF(PSException): pass
class PSSyntaxError(PSException): pass
class PSTypeError(PSException): pass
class PSValueError(PSException): pass


##  Basic PostScript Types
##

class PSObject:

    """Base class for all PS or PDF-related data types."""


class PSLiteral(PSObject):

    """A class that represents a PostScript literal.
    
    Postscript literals are used as identifiers, such as
    variable names, property names and dictionary keys.
    Literals are case sensitive and denoted by a preceding
    slash sign (e.g. "/Name")

    Note: Do not create an instance of PSLiteral directly.
    Always use PSLiteralTable.intern().
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '/%s' % self.name


class PSKeyword(PSObject):

    """A class that represents a PostScript keyword.
    
    PostScript keywords are a dozen of predefined words.
    Commands and directives in PostScript are expressed by keywords.
    They are also used to denote the content boundaries.
    
    Note: Do not create an instance of PSKeyword directly.
    Always use PSKeywordTable.intern().
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class PSSymbolTable:

    """A utility class for storing PSLiteral/PSKeyword objects.

    Interned objects can be checked its identity with "is" operator.
    """
    
    def __init__(self, klass):
        self.dict = {}
        self.klass = klass

    def intern(self, name):
        if name in self.dict:
            lit = self.dict[name]
        else:
            lit = self.klass(name)
            self.dict[name] = lit
        return lit

PSLiteralTable = PSSymbolTable(PSLiteral)
PSKeywordTable = PSSymbolTable(PSKeyword)
LIT = PSLiteralTable.intern
KWD = PSKeywordTable.intern
KEYWORD_PROC_BEGIN = KWD('{')
KEYWORD_PROC_END = KWD('}')
KEYWORD_ARRAY_BEGIN = KWD('[')
KEYWORD_ARRAY_END = KWD(']')
KEYWORD_DICT_BEGIN = KWD('<<')
KEYWORD_DICT_END = KWD('>>')


def literal_name(x):
    if not isinstance(x, PSLiteral):
        if STRICT:
            raise PSTypeError('Literal required: %r' % x)
        else:
            return str(x)
    return x.name

def keyword_name(x):
    if not isinstance(x, PSKeyword):
        if STRICT:
            raise PSTypeError('Keyword required: %r' % x)
        else:
            return str(x)
    return x.name


##  About PSParser, bytes and strings and all that
##  
##  Most of the contents (well, maybe not in size, but in "parsing effort") of a PDF file is text,
##  but in some cases, namely streams, there's binary data involved. Because of this, file pointers
##  to the file to parse must be opened in binary mode. Conversion to text happen at a low level,
##  in fillbuf() and revreadlines(), so we can treat the stuff we read as text pretty much
##  transparently. We use errors='replace' during decoding because this data will not be interpreted
##  by the 'normal parsing mechanism'. The stream parser reads directly to the file pointer, without
##  going through the buffer, so we get binary data.

EOL = re.compile(r'[\r\n]')
class PSBaseParser:

    """Most basic PostScript parser that performs only tokenization.
    """
    BUFSIZ = 4096

    debug = 0

    def __init__(self, fp):
        self.fp = fp
        self.is_eof = False
        self.lex = None
        self.seek(0)

    def __repr__(self):
        return '<%s: %r, bufpos=%d>' % (self.__class__.__name__, self.fp, self.bufpos)

    def flush(self):
        pass

    def close(self):
        self.flush()

    def tell(self):
        return self.bufpos+self.charpos

    def seek(self, pos):
        """Seeks the parser to the given position.
        """
        if 2 <= self.debug:
            print('seek: %r' % pos, file=sys.stderr)
        self.fp.seek(pos)
        # reset the status for nextline()
        self.bufpos = pos
        self.buf = ''
        self.charpos = 0

    def _readbuf(self, force):
        if force:
            # The bufsize thing below is there so that it's possible to grow the buffer to multiple
            # bufsizes if there's a need for it (for a very weird lexer input for example)
            bufsize = self.BUFSIZ + (len(self.buf) - self.charpos)
            abspos = self.tell()
            self.fp.seek(abspos)
        else:
            bufsize = self.BUFSIZ
        self.bufpos = self.fp.tell()
        data = self.fp.read(bufsize)
        self.is_eof = len(data) < bufsize
        self.charpos = 0
        self.lex = None
        return data
    
    def fillbuf(self, force=False):
        # When force is true, it means that even if charpos < len(self.buf), we want the buffer
        # to be filled. So what will happen is that we'll check our current pos according to charpos
        # and then seek it and then fill the buf from there. That means that there can be some
        # overlapping between the end of our old buf and our new buf.
        if (not force) and (self.charpos < len(self.buf)):
            return
        # fetch next chunk.
        read_bytes = self._readbuf(force)
        if not isinstance(read_bytes, bytes):
            raise Exception("Files read with PSParser must be opened in binary mode")
        self.rawbuf = read_bytes
        self.buf = read_bytes.decode('latin-1')

    def nextline(self):
        """Fetches a next line that ends either with \\r or \\n.
        """
        linebuf = ''
        linepos = self.bufpos + self.charpos
        eol = False
        while 1:
            self.fillbuf()
            if eol:
                c = self.buf[self.charpos]
                # handle '\r\n'
                if c == '\n':
                    linebuf += c
                    self.charpos += 1
                break
            m = EOL.search(self.buf, self.charpos)
            if m:
                linebuf += self.buf[self.charpos:m.end(0)]
                self.charpos = m.end(0)
                if linebuf[-1] == '\r':
                    eol = True
                else:
                    break
            else:
                linebuf += self.buf[self.charpos:]
                self.charpos = len(self.buf)
        if 2 <= self.debug:
            print('nextline: %r' % ((linepos, linebuf),), file=sys.stderr)
        return (linepos, linebuf)

    def revreadlines(self):
        """Fetches a next line backword.

        This is used to locate the trailers at the end of a file.
        """
        self.fp.seek(0, 2)
        pos = self.fp.tell()
        buf = ''
        while 0 < pos:
            prevpos = pos
            pos = max(0, pos-self.BUFSIZ)
            self.fp.seek(pos)
            read_bytes = self.fp.read(prevpos-pos)
            if not read_bytes: break
            s = read_bytes.decode('latin-1')
            while True:
                n = max(s.rfind('\r'), s.rfind('\n'))
                if n == -1:
                    buf = s + buf
                    break
                yield s[n:]+buf
                s = s[:n]
                buf = ''
    
    def _convert_token(self, token):
        # converts `token` which comes from pslexer to a normal token.
        if token.type in {'KEYWORD', 'OPERATOR'}:
            return KWD(token.value)
        elif token.type == 'LITERAL':
            return LIT(token.value)
        else:
            return token.value
    
    def nexttoken(self):
        self.fillbuf()
        if self.lex is None:
            self.lex = pslexer.lexer.clone()
            self.lex.input(self.buf)
        token = self.lex.token()
        if self.lex.lexpos > len(self.buf):
            # we read over our current buffer, even if the current token is valid, it might be
            # incomplete. refill the buffer.
            if self.is_eof:
                raise PSEOF('Unexpected EOF')
            self.fillbuf(force=True)
            return self.nexttoken()
        else:
            assert token is not None
            tokenpos = token.lexpos + self.bufpos
            self.charpos = self.lex.lexpos
            if 2 <= self.debug:
                print('nexttoken: %r' % (token,), file=sys.stderr)
            return (tokenpos, self._convert_token(token))
    

class PSStackParser(PSBaseParser):

    def __init__(self, fp):
        PSBaseParser.__init__(self, fp)
        self.reset()

    def reset(self):
        self.context = []
        self.curtype = None
        self.curstack = []
        self.results = []

    def seek(self, pos):
        PSBaseParser.seek(self, pos)
        self.reset()

    def push(self, *objs):
        self.curstack.extend(objs)
    
    def pop(self, n):
        objs = self.curstack[-n:]
        self.curstack[-n:] = []
        return objs
    
    def popall(self):
        objs = self.curstack
        self.curstack = []
        return objs
    
    def add_results(self, *objs):
        if 2 <= self.debug:
            print('add_results: %r' % (objs,), file=sys.stderr)
        self.results.extend(objs)

    def start_type(self, pos, type):
        self.context.append((pos, self.curtype, self.curstack))
        (self.curtype, self.curstack) = (type, [])
        if 2 <= self.debug:
            print('start_type: pos=%r, type=%r' % (pos, type), file=sys.stderr)
    
    def end_type(self, type):
        if self.curtype != type:
            raise PSTypeError('Type mismatch: %r != %r' % (self.curtype, type))
        objs = [ obj for (_,obj) in self.curstack ]
        (pos, self.curtype, self.curstack) = self.context.pop()
        if 2 <= self.debug:
            print('end_type: pos=%r, type=%r, objs=%r' % (pos, type, objs), file=sys.stderr)
        return (pos, objs)

    def do_keyword(self, pos, token):
        pass

    def nextobject(self):
        """Yields a list of objects.

        Returns keywords, literals, strings, numbers, arrays and dictionaries.
        Arrays and dictionaries are represented as Python lists and dictionaries.
        """
        while not self.results:
            (pos, token) = self.nexttoken()
            #print (pos,token), (self.curtype, self.curstack)
            if isinstance(token, (int, float, bool, str, bytes, PSLiteral)):
                # normal token
                self.push((pos, token))
            elif token == KEYWORD_ARRAY_BEGIN:
                # begin array
                self.start_type(pos, 'a')
            elif token == KEYWORD_ARRAY_END:
                # end array
                try:
                    self.push(self.end_type('a'))
                except PSTypeError:
                    if STRICT: raise
            elif token == KEYWORD_DICT_BEGIN:
                # begin dictionary
                self.start_type(pos, 'd')
            elif token == KEYWORD_DICT_END:
                # end dictionary
                try:
                    (pos, objs) = self.end_type('d')
                    if len(objs) % 2 != 0:
                        raise PSSyntaxError('Invalid dictionary construct: %r' % objs)
                    # construct a Python dictionary.
                    d = dict( (literal_name(k), v) for (k,v) in choplist(2, objs) if v is not None )
                    self.push((pos, d))
                except PSTypeError:
                    if STRICT: raise
            elif token == KEYWORD_PROC_BEGIN:
                # begin proc
                self.start_type(pos, 'p')
            elif token == KEYWORD_PROC_END:
                # end proc
                try:
                    self.push(self.end_type('p'))
                except PSTypeError:
                    if STRICT: raise
            else:
                if 2 <= self.debug:
                    print('do_keyword: pos=%r, token=%r, stack=%r' % \
                          (pos, token, self.curstack), file=sys.stderr)
                self.do_keyword(pos, token)
            if self.context:
                continue
            else:
                self.flush()
        obj = self.results.pop(0)
        if 2 <= self.debug:
            print('nextobject: %r' % (obj,), file=sys.stderr)
        return obj
