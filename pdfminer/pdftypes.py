from functools import partial
import zlib
from .lzw import lzwdecode
from .ascii85 import ascii85decode, asciihexdecode
from .runlength import rldecode
from .psparser import PSException, PSObject, STRICT
from .psparser import LIT, handle_error
from .utils import apply_png_predictor

LITERAL_CRYPT = LIT('Crypt')

# Abbreviation of Filter names in PDF 4.8.6. "Inline Images"
LITERALS_FLATE_DECODE = (LIT('FlateDecode'), LIT('Fl'))
LITERALS_LZW_DECODE = (LIT('LZWDecode'), LIT('LZW'))
LITERALS_ASCII85_DECODE = (LIT('ASCII85Decode'), LIT('A85'))
LITERALS_ASCIIHEX_DECODE = (LIT('ASCIIHexDecode'), LIT('AHx'))
LITERALS_RUNLENGTH_DECODE = (LIT('RunLengthDecode'), LIT('RL'))
LITERALS_CCITTFAX_DECODE = (LIT('CCITTFaxDecode'), LIT('CCF'))
LITERALS_DCT_DECODE = (LIT('DCTDecode'), LIT('DCT'))


##  PDF Objects
##
class PDFObject(PSObject): pass

class PDFException(PSException): pass
class PDFTypeError(PDFException): pass
class PDFValueError(PDFException): pass
class PDFNotImplementedError(PSException): pass


##  PDFObjRef
##
class PDFObjRef(PDFObject):

    def __init__(self, doc, objid, _):
        if objid == 0:
            handle_error(PDFValueError, 'PDF object id cannot be 0.')
        self.doc = doc
        self.objid = objid
        #self.genno = genno  # Never used.

    def __repr__(self):
        return '<PDFObjRef:%d>' % (self.objid)

    def resolve(self):
        return self.doc.getobj(self.objid)


# resolve
def resolve1(x):
    """Resolves an object.

    If this is an array or dictionary, it may still contains
    some indirect objects inside.
    """
    while isinstance(x, PDFObjRef):
        x = x.resolve()
    return x

def resolve_all(x):
    """Recursively resolves the given object and all the internals.
    
    Make sure there is no indirect reference within the nested object.
    This procedure might be slow.
    """
    while isinstance(x, PDFObjRef):
        x = x.resolve()
    if isinstance(x, list):
        x = [ resolve_all(v) for v in x ]
    elif isinstance(x, dict):
        for (k,v) in x.items():
            x[k] = resolve_all(v)
    return x

def decipher_all(decipher, objid, genno, x):
    """Recursively deciphers the given object.
    """
    if isinstance(x, str):
        x = x.encode('latin-1')
    if isinstance(x, bytes):
        return decipher(objid, genno, x)
    if isinstance(x, list):
        x = [ decipher_all(decipher, objid, genno, v) for v in x ]
    elif isinstance(x, dict):
        for (k,v) in x.items():
            x[k] = decipher_all(decipher, objid, genno, v)
    return x

# Type cheking
def typecheck_value(x, type, strict=STRICT):
    x = resolve1(x)
    if not isinstance(x, type):
        handle_error(PDFTypeError, 'Wrong type: %r required: %r' % (x, type), strict=strict)
        default_type = type[0] if isinstance(type, tuple) else type
        return default_type()
    return x

int_value = partial(typecheck_value, type=int)
float_value = partial(typecheck_value, type=float)
num_value = partial(typecheck_value, type=(int, float))
str_value = partial(typecheck_value, type=(str, bytes))
list_value = partial(typecheck_value, type=(list, tuple))
dict_value = partial(typecheck_value, type=dict)

def stream_value(x):
    x = resolve1(x)
    if not isinstance(x, PDFStream):
        handle_error(PDFTypeError, 'PDFStream required: %r' % x)
        return PDFStream({}, b'')
    return x


class PDFStream(PDFObject):

    def __init__(self, attrs, rawdata, decipher=None):
        assert isinstance(attrs, dict)
        self.attrs = attrs
        self.rawdata = rawdata
        self.decipher = decipher
        self.data = None
        self.objid = None
        self.genno = None

    def set_objid(self, objid, genno):
        self.objid = objid
        self.genno = genno

    def __repr__(self):
        if self.data is None:
            assert self.rawdata is not None
            return '<PDFStream(%r): raw=%d, %r>' % (self.objid, len(self.rawdata), self.attrs)
        else:
            assert self.data is not None
            return '<PDFStream(%r): len=%d, %r>' % (self.objid, len(self.data), self.attrs)

    def __contains__(self, name):
        return name in self.attrs
    
    def __getitem__(self, name):
        return self.attrs[name]
    
    def get(self, name, default=None):
        return self.attrs.get(name, default)
    
    def get_any(self, names, default=None):
        for name in names:
            if name in self.attrs:
                return self.attrs[name]
        return default

    def get_filters(self):
        filters = self.get_any(('F', 'Filter'))
        if not filters: return []
        if isinstance(filters, list): return filters
        return [ filters ]

    def decode(self):
        assert self.data is None and self.rawdata != None
        data = self.rawdata
        if self.decipher:
            # Handle encryption
            data = self.decipher(self.objid, self.genno, data)
        filters = self.get_filters()
        if not filters:
            self.data = data
            self.rawdata = None
            return
        for f in filters:
            # Yeah, we can have references to an object containing a literal.
            f = resolve1(f)
            if f is None:
                # Oops, broken reference. use FlateDecode since it's the most popular.
                f = LIT('FlateDecode')
            if f in LITERALS_FLATE_DECODE:
                # will get errors if the document is encrypted.
                try:
                    data = zlib.decompress(data)
                except zlib.error as e:
                    handle_error(PDFException, 'Invalid zlib bytes: %r, %r' % (e, data))
                    data = b''
            elif f in LITERALS_LZW_DECODE:
                data = lzwdecode(data)
            elif f in LITERALS_ASCII85_DECODE:
                data = ascii85decode(data)
            elif f in LITERALS_ASCIIHEX_DECODE:
                data = asciihexdecode(data)
            elif f in LITERALS_RUNLENGTH_DECODE:
                data = rldecode(data)
            elif f in LITERALS_DCT_DECODE:
                # /DCTDecode is essentially a jpeg image. There's nothing to "decode" per se, simply
                # use the data as jpeg data.
                pass
            elif f in LITERALS_CCITTFAX_DECODE:
                #data = ccittfaxdecode(data)
                raise PDFNotImplementedError('Unsupported filter: %r' % f)
            elif f == LITERAL_CRYPT:
                # not yet..
                raise PDFNotImplementedError('/Crypt filter is unsupported')
            else:
                raise PDFNotImplementedError('Unsupported filter: %r' % f)
            # apply predictors
            params = self.get_any(('DP', 'DecodeParms', 'FDecodeParms'), {})
            if 'Predictor' in params:
                pred = int_value(params['Predictor'])
                if pred == 1:
                    # no predictor
                    pass
                elif 10 <= pred:
                    # PNG predictor
                    colors = int_value(params.get('Colors', 1))
                    columns = int_value(params.get('Columns', 1))
                    bitspercomponent = int_value(params.get('BitsPerComponent', 8))
                    try:
                        data = apply_png_predictor(pred, colors, columns, bitspercomponent, data)
                    except ValueError: # predictor not supported
                        data = b''
                else:
                    raise PDFNotImplementedError('Unsupported predictor: %r' % pred)
        self.data = data
        self.rawdata = None

    def get_data(self):
        if self.data is None:
            self.decode()
        return self.data

    def get_rawdata(self):
        return self.rawdata
