import re
import logging

from .utils import choplist
from . import pslexer

STRICT = False


##  PS Exceptions
##
class PSException(Exception): pass
class PSEOF(PSException): pass
class PSSyntaxError(PSException): pass
class PSTypeError(PSException): pass
class PSValueError(PSException): pass

def handle_error(exctype, msg, strict=STRICT):
    if strict:
        raise exctype(msg)
    else:
        logging.warning(msg)

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
        handle_error(PSTypeError, 'Literal required: %r' % x)
        return str(x)
    return x.name

def keyword_name(x):
    if not isinstance(x, PSKeyword):
        handle_error(PSTypeError, 'Keyword required: %r' % x)
        return str(x)
    return x.name


##  About PSParser, bytes and strings and all that
##  
##  Most of the contents (well, maybe not in size, but in "parsing effort") of a PDF file is text,
##  but in some cases, namely streams, there's binary data involved. What we do is that we read the
##  data as latin-1. When binary data is encountered, we have to re-encode it as latin-1 as well.

##  About reading all data at once
##  There used to be a buffering mechanism in place, but it made everything rather complicated and
##  all this string buffering operations, especially with the ply lexer, ended up being rather slow.
##  We read the whole thing in memory now. Sure, some PDFs are rather large, but computers today
##  have lots of memory. At first, I wanted to use a mmap, but these are binary and making them work
## with the ply lexer was very complicated. Maybe one day.

EOL = re.compile(r'\r\n|\r|\n', re.MULTILINE)
class PSBaseParser:

    """Most basic PostScript parser that performs only tokenization.
    """
    def __init__(self, fp):
        data = fp.read()
        if isinstance(data, bytes):
            data = data.decode('latin-1')
        self.data = data
        self.lex = pslexer.lexer.clone()
        self.lex.input(data)

    def _convert_token(self, token):
        # converts `token` which comes from pslexer to a normal token.
        if token.type in {'KEYWORD', 'OPERATOR'}:
            if token.value == 'true':
                return True
            elif token.value == 'false':
                return False
            else:
                return KWD(token.value)
        elif token.type == 'LITERAL':
            return LIT(token.value)
        else:
            return token.value
    
    def flush(self):
        pass

    def close(self):
        self.flush()
        del self.lex
        del self.data
    
    def setpos(self, newpos):
        if newpos >= self.lex.lexlen:
            raise PSEOF()
        self.lex.lexpos = newpos
    
    def nextline(self):
        m = EOL.search(self.data, pos=self.lex.lexpos)
        if m is None:
            raise PSEOF()
        start = self.lex.lexpos
        s = self.data[start:m.end()]
        self.lex.lexpos = m.end()
        return (start, s)
    
    def nexttoken(self):
        token = self.lex.token()
        if token is None:
            raise PSEOF()
        tokenpos = token.lexpos
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

    def setpos(self, newpos):
        PSBaseParser.setpos(self, newpos)
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
        # logging.debug('add_results: %r', objs)
        self.results.extend(objs)

    def start_type(self, pos, type):
        self.context.append((pos, self.curtype, self.curstack))
        (self.curtype, self.curstack) = (type, [])
        # logging.debug('start_type: pos=%r, type=%r', pos, type)
    
    def end_type(self, type):
        if self.curtype != type:
            raise PSTypeError('Type mismatch: %r != %r' % (self.curtype, type))
        objs = [ obj for (_,obj) in self.curstack ]
        (pos, self.curtype, self.curstack) = self.context.pop()
        # logging.debug('end_type: pos=%r, type=%r, objs=%r', pos, type, objs)
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
                except PSTypeError as e:
                    handle_error(type(e), str(e))
            elif token == KEYWORD_DICT_BEGIN:
                # begin dictionary
                self.start_type(pos, 'd')
            elif token == KEYWORD_DICT_END:
                # end dictionary
                try:
                    (pos, objs) = self.end_type('d')
                    if len(objs) % 2 != 0:
                        handle_error(PSSyntaxError, 'Invalid dictionary construct: %r' % objs)
                    # construct a Python dictionary.
                    d = dict( (literal_name(k), v) for (k,v) in choplist(2, objs) if v is not None )
                    self.push((pos, d))
                except PSTypeError as e:
                    handle_error(type(e), str(e))
            elif token == KEYWORD_PROC_BEGIN:
                # begin proc
                self.start_type(pos, 'p')
            elif token == KEYWORD_PROC_END:
                # end proc
                try:
                    self.push(self.end_type('p'))
                except PSTypeError as e:
                    handle_error(type(e), str(e))
            else:
                logging.debug('do_keyword: pos=%r, token=%r, stack=%r', pos, token, self.curstack)
                self.do_keyword(pos, token)
            if self.context:
                continue
            else:
                self.flush()
        obj = self.results.pop(0)
        logging.debug('nextobject: %r', obj)
        return obj
