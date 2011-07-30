import struct
from sys import maxsize as INF


##  PNG Predictor
##
def apply_png_predictor(pred, colors, columns, bitspercomponent, data):
    if bitspercomponent != 8:
        # unsupported
        raise ValueError(bitspercomponent)
    nbytes = colors*columns*bitspercomponent//8
    i = 0
    buf = b''
    line0 = b'\x00' * columns
    while i < len(data):
        pred = data[i]
        i += 1
        line1 = data[i:i+nbytes]
        i += nbytes
        if pred == 0:
            # PNG none
            buf += line1
        elif pred == 1:
            # PNG sub (UNTESTED)
            c = 0
            bufline = []
            for b in line1:
                c = (c+b) & 255
                bufline.append(c)
            buf += bytes(bufline)
        elif pred == 2:
            # PNG up
            bufline = []
            for (a,b) in zip(line0,line1):
                c = (a+b) & 255
                bufline.append(c)
            buf += bytes(bufline)
        elif pred == 3:
            # PNG average (UNTESTED)
            c = 0
            bufline = []
            for (a,b) in zip(line0,line1):
                c = ((c+a+b)//2) & 255
                bufline.append(c)
            buf += bytes(bufline)
        else:
            # unsupported
            raise ValueError(pred)
        line0 = line1
    return buf


##  Matrix operations
##
MATRIX_IDENTITY = (1, 0, 0, 1, 0, 0)

def mult_matrix(matrix1, matrix2):
    """Returns the multiplication of two matrices."""
    (a1,b1,c1,d1,e1,f1) = matrix1
    (a0,b0,c0,d0,e0,f0) = matrix2
    return (a0*a1+c0*b1,    b0*a1+d0*b1,
            a0*c1+c0*d1,    b0*c1+d0*d1,
            a0*e1+c0*f1+e0, b0*e1+d0*f1+f0)

def translate_matrix(matrix, point):
    """Translates a matrix by (x,y)."""
    (a,b,c,d,e,f) = matrix
    (x,y) = point
    return (a,b,c,d,x*a+y*c+e,x*b+y*d+f)

def apply_matrix_pt(matrix, point):
    """Applies a matrix to a point."""
    (a,b,c,d,e,f) = matrix
    (x,y) = point
    return (a*x+c*y+e, b*x+d*y+f)

def apply_matrix_norm(matrix, norm):
    """Equivalent to apply_matrix_pt(M, (p,q)) - apply_matrix_pt(M, (0,0))"""
    (a,b,c,d,e,f) = matrix
    (p,q) = norm
    return (a*p+c*q, b*p+d*q)


##  Utility functions
##

# uniq
def uniq(objs):
    """Eliminates duplicated elements."""
    done = set()
    for obj in objs:
        if obj in done: continue
        done.add(obj)
        yield obj

# fsplit
def fsplit(pred, objs):
    """Split a list into two classes according to the predicate."""
    t = []
    f = []
    for obj in objs:
        if pred(obj):
            t.append(obj)
        else:
            f.append(obj)
    return (t,f)

# drange
def drange(v0, v1, d):
    """Returns a discrete range."""
    assert v0 < v1
    return range(int(v0)//d, int(v1+d)//d)

# get_bound
def get_bound(pts):
    """Compute a minimal rectangle that covers all the points."""
    (x0, y0, x1, y1) = (INF, INF, -INF, -INF)
    for (x,y) in pts:
        x0 = min(x0, x)
        y0 = min(y0, y)
        x1 = max(x1, x)
        y1 = max(y1, y)
    return (x0,y0,x1,y1)

# pick
def pick(seq, func, maxobj=None):
    """Picks the object obj where func(obj) has the highest value."""
    maxscore = None
    for obj in seq:
        score = func(obj)
        if maxscore is None or maxscore < score:
            (maxscore,maxobj) = (score,obj)
    return maxobj

# choplist
def choplist(n, seq):
    """Groups every n elements of the list."""
    r = []
    for x in seq:
        r.append(x)
        if len(r) == n:
            yield tuple(r)
            r = []

def trailiter(iterable, skipfirst=False):
    """Yields (prev_element, element), starting with (None, first_element).
    
    If skipfirst is True, there will be no (None, item1) element and we'll start
    directly with (item1, item2).
    """
    it = iter(iterable)
    if skipfirst:
        prev = next(it)
    else:
        prev = None
    for item in it:
        yield prev, item
        prev = item

# nunpack
def nunpack(b, default=0):
    """Unpacks 1 to 4 byte integers (big endian)."""
    if isinstance(b, str):
        b = b.encode('latin-1')
    l = len(b)
    if not l:
        return default
    elif l == 1:
        return b[0]
    elif l == 2:
        return struct.unpack(b'>H', b)[0]
    elif l == 3:
        return struct.unpack(b'>L', b'\x00'+b)[0]
    elif l == 4:
        return struct.unpack(b'>L', b)[0]
    else:
        raise TypeError('invalid length: %d' % l)

# decode_text
PDFDocEncoding = ''.join( chr(x) for x in (
  0x0000, 0x0001, 0x0002, 0x0003, 0x0004, 0x0005, 0x0006, 0x0007,
  0x0008, 0x0009, 0x000a, 0x000b, 0x000c, 0x000d, 0x000e, 0x000f,
  0x0010, 0x0011, 0x0012, 0x0013, 0x0014, 0x0015, 0x0017, 0x0017,
  0x02d8, 0x02c7, 0x02c6, 0x02d9, 0x02dd, 0x02db, 0x02da, 0x02dc,
  0x0020, 0x0021, 0x0022, 0x0023, 0x0024, 0x0025, 0x0026, 0x0027,
  0x0028, 0x0029, 0x002a, 0x002b, 0x002c, 0x002d, 0x002e, 0x002f,
  0x0030, 0x0031, 0x0032, 0x0033, 0x0034, 0x0035, 0x0036, 0x0037,
  0x0038, 0x0039, 0x003a, 0x003b, 0x003c, 0x003d, 0x003e, 0x003f,
  0x0040, 0x0041, 0x0042, 0x0043, 0x0044, 0x0045, 0x0046, 0x0047,
  0x0048, 0x0049, 0x004a, 0x004b, 0x004c, 0x004d, 0x004e, 0x004f,
  0x0050, 0x0051, 0x0052, 0x0053, 0x0054, 0x0055, 0x0056, 0x0057,
  0x0058, 0x0059, 0x005a, 0x005b, 0x005c, 0x005d, 0x005e, 0x005f,
  0x0060, 0x0061, 0x0062, 0x0063, 0x0064, 0x0065, 0x0066, 0x0067,
  0x0068, 0x0069, 0x006a, 0x006b, 0x006c, 0x006d, 0x006e, 0x006f,
  0x0070, 0x0071, 0x0072, 0x0073, 0x0074, 0x0075, 0x0076, 0x0077,
  0x0078, 0x0079, 0x007a, 0x007b, 0x007c, 0x007d, 0x007e, 0x0000,
  0x2022, 0x2020, 0x2021, 0x2026, 0x2014, 0x2013, 0x0192, 0x2044,
  0x2039, 0x203a, 0x2212, 0x2030, 0x201e, 0x201c, 0x201d, 0x2018,
  0x2019, 0x201a, 0x2122, 0xfb01, 0xfb02, 0x0141, 0x0152, 0x0160,
  0x0178, 0x017d, 0x0131, 0x0142, 0x0153, 0x0161, 0x017e, 0x0000,
  0x20ac, 0x00a1, 0x00a2, 0x00a3, 0x00a4, 0x00a5, 0x00a6, 0x00a7,
  0x00a8, 0x00a9, 0x00aa, 0x00ab, 0x00ac, 0x0000, 0x00ae, 0x00af,
  0x00b0, 0x00b1, 0x00b2, 0x00b3, 0x00b4, 0x00b5, 0x00b6, 0x00b7,
  0x00b8, 0x00b9, 0x00ba, 0x00bb, 0x00bc, 0x00bd, 0x00be, 0x00bf,
  0x00c0, 0x00c1, 0x00c2, 0x00c3, 0x00c4, 0x00c5, 0x00c6, 0x00c7,
  0x00c8, 0x00c9, 0x00ca, 0x00cb, 0x00cc, 0x00cd, 0x00ce, 0x00cf,
  0x00d0, 0x00d1, 0x00d2, 0x00d3, 0x00d4, 0x00d5, 0x00d6, 0x00d7,
  0x00d8, 0x00d9, 0x00da, 0x00db, 0x00dc, 0x00dd, 0x00de, 0x00df,
  0x00e0, 0x00e1, 0x00e2, 0x00e3, 0x00e4, 0x00e5, 0x00e6, 0x00e7,
  0x00e8, 0x00e9, 0x00ea, 0x00eb, 0x00ec, 0x00ed, 0x00ee, 0x00ef,
  0x00f0, 0x00f1, 0x00f2, 0x00f3, 0x00f4, 0x00f5, 0x00f6, 0x00f7,
  0x00f8, 0x00f9, 0x00fa, 0x00fb, 0x00fc, 0x00fd, 0x00fe, 0x00ff,
))
def decode_text(s):
    """Decodes a PDFDocEncoding string to Unicode."""
    if s.startswith('\xfe\xff'):
        return str(s[2:], 'utf-16be', 'ignore')
    else:
        return ''.join( PDFDocEncoding[ord(c)] for c in s )

def htmlescape(s, encoding='ascii'):
    """Escapes a string for SGML/XML/HTML"""
    s = s.replace('&','&amp;').replace('>','&gt;').replace('<','&lt;').replace('"','&quot;')
    # Additionally to basic replaces, we also make sure that all characters are convertible to our
    # target encoding. If they're not, they're replaced by XML entities.
    encoded = s.encode(encoding, errors='xmlcharrefreplace')
    return encoded.decode(encoding)

def bbox2str(bbox):
    (x0,y0,x1,y1) = bbox
    return '%.3f,%.3f,%.3f,%.3f' % (x0, y0, x1, y1)

def matrix2str(matrix):
    (a,b,c,d,e,f) = matrix
    return '[%.2f,%.2f,%.2f,%.2f, (%.2f,%.2f)]' % (a,b,c,d,e,f)

def set_debug_logging():
    import logging, sys
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

class ObjIdRange:

    "A utility class to represent a range of object IDs."
    
    def __init__(self, start, nobjs):
        self.start = start
        self.nobjs = nobjs

    def __repr__(self):
        return '<ObjIdRange: %d-%d>' % (self.get_start_id(), self.get_end_id())

    def get_start_id(self):
        return self.start

    def get_end_id(self):
        return self.start + self.nobjs - 1

    def get_nobjs(self):
        return self.nobjs


# create_bmp
def create_bmp(data, bits, width, height):
    info = struct.pack('<IiiHHIIIIII', 40, width, height, 1, bits, 0, len(data), 0, 0, 0, 0)
    assert len(info) == 40, len(info)
    header = struct.pack('<ccIHHI', 'B', 'M', 14+40+len(data), 0, 0, 14+40)
    assert len(header) == 14, len(header)
    # XXX re-rasterize every line
    return header+info+data
