import io
import re
import struct
import hashlib as md5
import logging

from .psparser import PSStackParser, PSSyntaxError, PSEOF, literal_name, LIT, KWD, handle_error
from .pdftypes import (PDFException, PDFTypeError, PDFNotImplementedError, PDFStream, PDFObjRef,
    resolve1, decipher_all, int_value, str_value, list_value, dict_value, stream_value)
from .arcfour import Arcfour
from .utils import choplist, nunpack, decode_text, ObjIdRange


logger = logging.getLogger(__name__)


##  Exceptions
##
class PDFSyntaxError(PDFException): pass
class PDFNoValidXRef(PDFSyntaxError): pass
class PDFNoOutlines(PDFException): pass
class PDFDestinationNotFound(PDFException): pass
class PDFAlreadyParsed(PDFException): pass
class PDFEncryptionError(PDFException): pass
class PDFPasswordIncorrect(PDFEncryptionError): pass

# some predefined literals and keywords.
LITERAL_OBJSTM = LIT('ObjStm')
LITERAL_XREF = LIT('XRef')
LITERAL_PAGE = LIT('Page')
LITERAL_PAGES = LIT('Pages')
LITERAL_CATALOG = LIT('Catalog')


class PDFBaseXRef:

    def get_trailer(self):
        raise NotImplementedError

    def get_objids(self):
        return []

    def get_pos(self, objid):
        raise KeyError(objid)


class PDFXRef(PDFBaseXRef):
    
    def __init__(self):
        self.offsets = {}
        self.trailer = {}

    def load(self, parser):
        while 1:
            try:
                (pos, line) = parser.nextline()
                if not line.strip(): continue
            except PSEOF:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
            if not line:
                raise PDFNoValidXRef('Premature eof: %r' % parser)
            if line.startswith('trailer'):
                parser.setpos(pos)
                break
            f = line.strip().split(' ')
            if len(f) != 2:
                raise PDFNoValidXRef('Trailer not found: %r: line=%r' % (parser, line))
            try:
                (start, nobjs) = list(map(int, f))
            except ValueError:
                raise PDFNoValidXRef('Invalid line: %r: line=%r' % (parser, line))
            for objid in range(start, start+nobjs):
                try:
                    (_, line) = parser.nextline()
                except PSEOF:
                    raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
                f = line.strip().split(' ')
                if len(f) != 3:
                    raise PDFNoValidXRef('Invalid XRef format: %r, line=%r' % (parser, line))
                (pos, genno, use) = f
                if use != 'n': continue
                self.offsets[objid] = (int(genno), int(pos))
        logger.debug('xref objects: %r', self.offsets)
        self.load_trailer(parser)

    KEYWORD_TRAILER = KWD('trailer')
    def load_trailer(self, parser):
        try:
            (_,kwd) = parser.nexttoken()
            assert kwd is self.KEYWORD_TRAILER
            (_,dic) = parser.nextobject()
        except PSEOF:
            x = parser.pop(1)
            if not x:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted')
            (_,dic) = x[0]
        self.trailer.update(dict_value(dic))

    PDFOBJ_CUE = re.compile(r'^(\d+)\s+(\d+)\s+obj\b')

    def load_fallback(self, parser, debug=0):
        parser.setpos(0)
        while 1:
            try:
                (pos, line) = parser.nextline()
            except PSEOF:
                break
            if line.startswith('trailer'):
                parser.setpos(pos)
                self.load_trailer(parser)
                logger.debug('trailer: %r', self.get_trailer())
                break
            m = self.PDFOBJ_CUE.match(line)
            if not m: continue
            (objid, genno) = m.groups()
            self.offsets[int(objid)] = (0, pos)

    def get_trailer(self):
        return self.trailer

    def get_objids(self):
        return iter(self.offsets.keys())

    def get_pos(self, objid):
        try:
            (genno, pos) = self.offsets[objid]
        except KeyError:
            raise
        return (None, pos)


class PDFXRefStream(PDFBaseXRef):

    def __init__(self):
        self.data = None
        self.entlen = None
        self.fl1 = self.fl2 = self.fl3 = None
        self.objid_ranges = []

    def __repr__(self):
        return '<PDFXRefStream: fields=%d,%d,%d>' % (self.fl1, self.fl2, self.fl3)

    def load(self, parser):
        (_,objid) = parser.nexttoken() # ignored
        (_,genno) = parser.nexttoken() # ignored
        (_,kwd) = parser.nexttoken()
        (_,stream) = parser.nextobject()
        if not isinstance(stream, PDFStream) or stream['Type'] is not LITERAL_XREF:
            raise PDFNoValidXRef('Invalid PDF stream spec.')
        size = stream['Size']
        index_array = stream.get('Index', (0,size))
        if len(index_array) % 2 != 0:
            raise PDFSyntaxError('Invalid index number')
        self.objid_ranges.extend( ObjIdRange(start, nobjs) 
                                  for (start,nobjs) in choplist(2, index_array) )
        (self.fl1, self.fl2, self.fl3) = stream['W']
        self.data = stream.get_data()
        self.entlen = self.fl1+self.fl2+self.fl3
        self.trailer = stream.attrs
        if logger.getEffectiveLevel() <= logging.DEBUG:
            logger.debug('xref stream: objid=%s, fields=%d,%d,%d',
                ', '.join(map(repr, self.objid_ranges)), self.fl1, self.fl2, self.fl3)

    def get_trailer(self):
        return self.trailer

    def get_objids(self):
        for objid_range in self.objid_ranges:
            for x in range(objid_range.get_start_id(), objid_range.get_end_id()+1):
                yield x

    def get_pos(self, objid):
        offset = 0
        found = False
        for objid_range in self.objid_ranges:
            if objid >= objid_range.get_start_id() and objid <= objid_range.get_end_id():
                offset += objid - objid_range.get_start_id()
                found = True
                break
            else:
                offset += objid_range.get_nobjs()
        if not found: raise KeyError(objid)
        i = self.entlen * offset
        ent = self.data[i:i+self.entlen]
        f1 = nunpack(ent[:self.fl1], 1)
        if f1 == 1:
            pos = nunpack(ent[self.fl1:self.fl1+self.fl2])
            genno = nunpack(ent[self.fl1+self.fl2:])
            return (None, pos)
        elif f1 == 2:
            objid = nunpack(ent[self.fl1:self.fl1+self.fl2])
            index = nunpack(ent[self.fl1+self.fl2:])
            return (objid, index)
        # this is a free object
        raise KeyError(objid)


class PDFPage:

    """An object that holds the information about a page.

    A PDFPage object is merely a convenience class that has a set
    of keys and values, which describe the properties of a page
    and point to its contents.

    Attributes:
      doc: a PDFDocument object.
      pageid: any Python object that can uniquely identify the page.
      attrs: a dictionary of page attributes.
      contents: a list of PDFStream objects that represents the page content.
      lastmod: the last modified time of the page.
      resources: a list of resources used by the page.
      mediabox: the physical size of the page.
      cropbox: the crop rectangle of the page.
      rotate: the page rotation (in degree).
      annots: the page annotations.
      beads: a chain that represents natural reading order.
    """

    def __init__(self, doc, pageid, attrs):
        """Initialize a page object.
        
        doc: a PDFDocument object.
        pageid: any Python object that can uniquely identify the page.
        attrs: a dictionary of page attributes.
        """
        self.doc = doc
        self.pageid = pageid
        self.attrs = dict_value(attrs)
        self.lastmod = resolve1(self.attrs.get('LastModified'))
        self.resources = resolve1(self.attrs['Resources'])
        self.mediabox = resolve1(self.attrs['MediaBox'])
        if 'CropBox' in self.attrs:
            self.cropbox = resolve1(self.attrs['CropBox'])
        else:
            self.cropbox = self.mediabox
        self.rotate = (self.attrs.get('Rotate', 0)+360) % 360
        self.annots = self.attrs.get('Annots')
        self.beads = self.attrs.get('B')
        if 'Contents' in self.attrs:
            contents = resolve1(self.attrs['Contents'])
        else:
            contents = []
        if not isinstance(contents, list):
            contents = [ contents ]
        self.contents = contents

    def __repr__(self):
        return '<PDFPage: Resources=%r, MediaBox=%r>' % (self.resources, self.mediabox)


class PDFDocument:
    """PDFDocument object represents a PDF document.

    Since a PDF file can be very big, normally it is not loaded at
    once. So PDF document has to cooperate with a PDF parser in order to
    dynamically import the data as processing goes.

    Typical usage:
      doc = PDFDocument()
      doc.set_parser(parser)
      doc.initialize(password)
      obj = doc.getobj(objid)
    
    """
    
    KEYWORD_OBJ = KWD('obj')

    def __init__(self, caching=True):
        self.caching = caching
        self.xrefs = []
        self.info = []
        self.catalog = None
        self.encryption = None
        self.decipher = None
        self._parser = None
        self._cached_objs = {}
        self._parsed_objs = {}
        self._parsed_everything = False
    
    def _parse_next_object(self, parser):
        # This is a bit awkward and I suspect that it could be a lot more elegant, but it would
        # require refactoring the parsing process and I don't want to do that yet.
        stack = []
        _, token = parser.nexttoken()
        while token is not self.KEYWORD_OBJ:
            stack.append(token)
            _, token = parser.nexttoken()
        objid = stack[-2]
        genno = stack[-1]
        _, obj = parser.nextobject()
        return objid, genno, obj
    
    def _parse_objstream(self, stream):
        # ObjStm have a special organization. First, the param "N" tells how many objs we have in
        # there. Then, they start with a list of (objids, genno) pairs, and then the actual objects
        # come in.
        parser = PDFStreamParser(stream.get_data())
        parser.set_document(self)
        objcount = stream['N']
        objids = []
        for i in range(objcount):
            _, objid = parser.nextobject()
            _, genno = parser.nextobject()
            objids.append(objid)
        # Now we should be at the point where we read objects
        for objid in objids:
            _, obj = parser.nextobject()
            self._cached_objs[objid] = obj
    
    def _parse_whole(self, parser):
        while True:
            try:
                objid, genno, obj = self._parse_next_object(parser)
                self._cached_objs[objid] = obj
                if isinstance(obj, PDFStream) and obj.get('Type') is LITERAL_OBJSTM:
                    obj.set_objid(objid, genno)
                    self._parse_objstream(obj)
            except PSEOF:
                break
    
    def _parse_everything(self):
        # Sometimes, we have malformed xref, but we still want to manage to read the PDF. In cases
        # like these, the last resort is to read all objects at once so that our object reference
        # can finally be resolved. This is slower than the normal method, so ony use this when the
        # xref tables are corrupt/wrong/whatever.
        if self._parsed_everything:
            raise PDFAlreadyParsed()
        parser = self._parser
        parser.setpos(0)
        parser.reset()
        self._parse_whole(parser)
        self._parsed_everything = True
    
    def _getobj(self, objid):
        if not self.xrefs:
            raise PDFException('PDFDocument is not initialized')
        # logger.debug('getobj: objid=%r', objid)
        if objid in self._cached_objs:
            genno = 0
            obj = self._cached_objs[objid]
        else:
            strmid, index = self.find_obj_ref(objid)
            if index is None:
                handle_error(PDFSyntaxError, 'Cannot locate objid=%r' % objid)
                # return null for a nonexistent reference.
                return None
            if strmid:
                stream = self.getobj(strmid)
                if stream is None:
                    return None
                stream = stream_value(stream)
                if stream.get('Type') is not LITERAL_OBJSTM:
                    handle_error(PDFSyntaxError, 'Not a stream object: %r' % stream)
                try:
                    n = stream['N']
                except KeyError:
                    handle_error(PDFSyntaxError, 'N is not defined: %r' % stream)
                    n = 0
                if strmid in self._parsed_objs:
                    objs = self._parsed_objs[strmid]
                else:
                    parser = PDFStreamParser(stream.get_data())
                    parser.set_document(self)
                    objs = []
                    try:
                        while True:
                            _, obj = parser.nextobject()
                            objs.append(obj)
                    except PSEOF:
                        pass
                    if self.caching:
                        self._parsed_objs[strmid] = objs
                genno = 0
                i = n*2+index
                try:
                    obj = objs[i]
                except IndexError:
                    raise PDFSyntaxError('Invalid object number: objid=%r' % (objid))
                if isinstance(obj, PDFStream):
                    obj.set_objid(objid, 0)
            else:
                try:
                    self._parser.setpos(index)
                except PSEOF:
                    handle_error(PSEOF, 'Parser index out of bounds')
                    return None
                (_,objid1) = self._parser.nexttoken() # objid
                (_,genno) = self._parser.nexttoken() # genno
                (_,kwd) = self._parser.nexttoken()
                # #### hack around malformed pdf files
                #assert objid1 == objid, (objid, objid1)
                if objid1 != objid:
                    x = []
                    while kwd is not self.KEYWORD_OBJ:
                        (_,kwd) = self._parser.nexttoken()
                        x.append(kwd)
                    if x:
                        objid1 = x[-2]
                        genno = x[-1]
                # #### end hack around malformed pdf files
                if kwd is not self.KEYWORD_OBJ:
                    raise PDFSyntaxError('Invalid object spec: offset=%r' % index)
                try:
                    (_,obj) = self._parser.nextobject()
                    if isinstance(obj, PDFStream):
                        obj.set_objid(objid, genno)
                except PSEOF:
                    return None
            # logger.debug('register: objid=%r: %r', objid, obj)
            if self.caching:
                self._cached_objs[objid] = obj
        if self.decipher:
            obj = decipher_all(self.decipher, objid, genno, obj)
        return obj
    
    def set_parser(self, parser):
        "Set the document to use a given PDFParser object."
        if self._parser:
            return
        self._parser = parser
        # Retrieve the information of each header that was appended
        # (maybe multiple times) at the end of the document.
        self.xrefs = parser.read_xref()
        for xref in self.xrefs:
            trailer = xref.get_trailer()
            if not trailer: continue
            # If there's an encryption info, remember it.
            if 'Encrypt' in trailer:
                #assert not self.encryption
                self.encryption = (list_value(trailer['ID']),
                                   dict_value(trailer['Encrypt']))
            if 'Info' in trailer:
                self.info.append(dict_value(trailer['Info']))
            if 'Root' in trailer:
                #  Every PDF file must have exactly one /Root dictionary.
                self.catalog = dict_value(trailer['Root'])
                break
        else:
            raise PDFSyntaxError('No /Root object! - Is this really a PDF?')
        if self.catalog.get('Type') is not LITERAL_CATALOG:
            handle_error(PDFSyntaxError, 'Catalog not found!')

    # initialize(password='')
    #   Perform the initialization with a given password.
    #   This step is mandatory even if there's no password associated
    #   with the document.
    PASSWORD_PADDING = b'(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08..\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz'
    def initialize(self, password=''):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            return
        (docid, param) = self.encryption
        if literal_name(param.get('Filter')) != 'Standard':
            raise PDFEncryptionError('Unknown filter: param=%r' % param)
        V = int_value(param.get('V', 0))
        if not (V == 1 or V == 2):
            raise PDFEncryptionError('Unknown algorithm: param=%r' % param)
        length = int_value(param.get('Length', 40)) # Key length (bits)
        O = str_value(param['O'])
        R = int_value(param['R']) # Revision
        if 5 <= R:
            raise PDFEncryptionError('Unknown revision: %r' % R)
        U = str_value(param['U'])
        P = int_value(param['P'])
        self.is_printable = bool(P & 4)
        self.is_modifiable = bool(P & 8)
        self.is_extractable = bool(P & 16)
        # Algorithm 3.2
        # XXX is latin-1 the correct encoding???
        password = password.encode('latin-1')
        password = (password+self.PASSWORD_PADDING)[:32] # 1
        hash = md5.md5(password) # 2
        hash.update(O) # 3
        hash.update(struct.pack('<l', P)) # 4
        hash.update(docid[0]) # 5
        if 4 <= R:
            # 6
            raise PDFNotImplementedError('Revision 4 encryption is currently unsupported')
        if 3 <= R:
            # 8
            for _ in range(50):
                hash = md5.md5(hash.digest()[:length//8])
        key = hash.digest()[:length//8]
        if R == 2:
            # Algorithm 3.4
            u1 = Arcfour(key).process(self.PASSWORD_PADDING)
        elif R == 3:
            # Algorithm 3.5
            hash = md5.md5(self.PASSWORD_PADDING) # 2
            hash.update(docid[0]) # 3
            x = Arcfour(key).process(hash.digest()[:16]) # 4
            for i in range(1,19+1):
                k = bytes( c ^ i for c in key )
                x = Arcfour(k).process(x)
            u1 = x+x # 32bytes total
        if R == 2:
            is_authenticated = (u1 == U)
        else:
            is_authenticated = (u1[:16] == U[:16])
        if not is_authenticated:
            raise PDFPasswordIncorrect
        self.decrypt_key = key
        self.decipher = self.decrypt_rc4  # XXX may be AES

    def decrypt_rc4(self, objid, genno, data):
        key = self.decrypt_key + struct.pack('<L',objid)[:3]+struct.pack('<L',genno)[:2]
        hash = md5.md5(key)
        key = hash.digest()[:min(len(key),16)]
        return Arcfour(key).process(data)
    
    def readobj(self):
        """Read the next object at current position.
        
        The object doesn't have to start exactly where we are. We'll read the first
        object that comes to us.
        """
        return self._parse_next_object(self._parser)
    
    def find_obj_ref(self, objid):
        for xref in self.xrefs:
            try:
                strmid, index = xref.get_pos(objid)
                return strmid, index
            except KeyError:
                pass
        else:
            # return null for a nonexistent reference.
            return None, None
    
    def getobj(self, objid):
        result = self._getobj(objid)
        if result is None:
            try:
                self._parse_everything()
                result = self._getobj(objid)
            except PDFAlreadyParsed:
                result = None
        return result
    
    INHERITABLE_ATTRS = {'Resources', 'MediaBox', 'CropBox', 'Rotate'}
    def get_pages(self):
        if not self.xrefs:
            raise PDFException('PDFDocument is not initialized')
        def search(obj, parent):
            try:
                if isinstance(obj, int):
                    objid = obj
                    tree = dict_value(self.getobj(objid), strict=True).copy()
                else:
                    objid = obj.objid
                    tree = dict_value(obj, strict=True).copy()
            except PDFTypeError:
                return
            for (k,v) in parent.items():
                if k in self.INHERITABLE_ATTRS and k not in tree:
                    tree[k] = v
            if tree.get('Type') is LITERAL_PAGES and 'Kids' in tree:
                logger.debug('Pages: Kids=%r', tree['Kids'])
                for c in list_value(tree['Kids']):
                    for x in search(c, tree):
                        yield x
            elif tree.get('Type') is LITERAL_PAGE:
                logger.debug('Page: %r', tree)
                yield (objid, tree)
        if 'Pages' not in self.catalog:
            return
        for (pageid,tree) in search(self.catalog['Pages'], self.catalog):
            yield PDFPage(self, pageid, tree)

    def get_outlines(self):
        if 'Outlines' not in self.catalog:
            raise PDFNoOutlines
        def search(entry, level):
            entry = dict_value(entry)
            if 'Title' in entry:
                if 'A' in entry or 'Dest' in entry:
                    title = decode_text(str_value(entry['Title']))
                    dest = entry.get('Dest')
                    action = entry.get('A')
                    se = entry.get('SE')
                    yield (level, title, dest, action, se)
            if 'First' in entry and 'Last' in entry:
                for x in search(entry['First'], level+1):
                    yield x
            if 'Next' in entry:
                for x in search(entry['Next'], level):
                    yield x
        return search(self.catalog['Outlines'], 0)

    def lookup_name(self, cat, key):
        try:
            names = dict_value(self.catalog['Names'])
        except (PDFTypeError, KeyError):
            raise KeyError((cat,key))
        # may raise KeyError
        d0 = dict_value(names[cat])
        def lookup(d):
            if 'Limits' in d:
                (k1,k2) = list_value(d['Limits'])
                if key < k1 or k2 < key: return None
                if 'Names' in d:
                    objs = list_value(d['Names'])
                    names = dict(choplist(2, objs))
                    return names[key]
            if 'Kids' in d:
                for c in list_value(d['Kids']):
                    v = lookup(dict_value(c))
                    if v: return v
            raise KeyError((cat,key))
        return lookup(d0)

    def get_dest(self, name):
        try:
            # PDF-1.2 or later
            obj = self.lookup_name('Dests', name)
        except KeyError:
            # PDF-1.1 or prior
            if 'Dests' not in self.catalog:
                raise PDFDestinationNotFound(name)
            d0 = dict_value(self.catalog['Dests'])
            if name not in d0:
                raise PDFDestinationNotFound(name)
            obj = d0[name]
        return obj


class PDFParser(PSStackParser):

    """
    PDFParser fetch PDF objects from a file stream.
    It can handle indirect references by referring to
    a PDF document set by set_document method.
    It also reads XRefs at the end of every PDF file.

    Typical usage:
      parser = PDFParser(fp)
      parser.read_xref()
      parser.set_document(doc)
      parser.seek(offset)
      parser.nextobject()
    
    """

    def __init__(self, fp):
        PSStackParser.__init__(self, fp)
        self.doc = None
        self.fallback = False

    def set_document(self, doc):
        """Associates the parser with a PDFDocument object."""
        self.doc = doc

    KEYWORD_R = KWD('R')
    KEYWORD_NULL = KWD('null')
    KEYWORD_ENDOBJ = KWD('endobj')
    KEYWORD_STREAM = KWD('stream')
    KEYWORD_XREF = KWD('xref')
    KEYWORD_STARTXREF = KWD('startxref')
    def do_keyword(self, pos, token):
        """Handles PDF-related keywords."""
        
        if token in (self.KEYWORD_XREF, self.KEYWORD_STARTXREF):
            self.add_results(*self.pop(1))
        
        elif token is self.KEYWORD_ENDOBJ:
            self.add_results(*self.pop(4))

        elif token is self.KEYWORD_NULL:
            # null object
            self.push((pos, None))

        elif token is self.KEYWORD_R:
            # reference to indirect object
            try:
                ((_,objid), (_,genno)) = self.pop(2)
                (objid, genno) = (int(objid), int(genno))
                obj = PDFObjRef(self.doc, objid, genno)
                self.push((pos, obj))
            except PSSyntaxError:
                pass

        elif token is self.KEYWORD_STREAM:
            # stream object
            ((_,dic),) = self.pop(1)
            dic = dict_value(dic)
            try:
                objlen = int_value(dic['Length'])
            except KeyError:
                handle_error(PDFSyntaxError, '/Length is undefined: %r' % dic)
                objlen = 0
            self.setpos(pos)
            try:
                (_, line) = self.nextline()  # 'stream'
            except PSEOF:
                handle_error(PDFSyntaxError, 'Unexpected EOF')
                return
            pos += len(line)
            endpos = pos + objlen
            if 'endstream' not in self.data[endpos:endpos+len('endstream')+2]:
                r = re.compile(r'(\r\n|\r|\n)endstream')
                m = r.search(self.data, pos)
                if m is None:
                    raise PDFSyntaxError("stream with no endstream")
                endpos = m.start()
            data = self.data[pos:endpos].encode('latin-1')
            self.setpos(endpos)
            self.nexttoken() # consume 'endstream'
            # XXX limit objlen not to exceed object boundary
            # logger.debug('Stream: pos=%d, objlen=%d, dic=%r, data=%r...', pos, objlen, dic, data[:10])
            obj = PDFStream(dic, data, self.doc.decipher)
            self.push((pos, obj))

        else:
            # others
            self.push((pos, token))
        

    def find_xref(self):
        """Internal function used to locate the first XRef."""
        # the word 'startxref' followed by a newline followed by digits
        re_startxref = re.compile(r'startxref\s*[\r\n]+\s*(\d+)', re.MULTILINE)
        # try at the end, then try the whole file.
        m = re_startxref.findall(self.data, len(self.data)-4096)
        if not m:
            m = re_startxref.findall(self.data)
        if not m:
            raise PDFNoValidXRef('Unexpected EOF')
        logger.debug('xref found: pos=%r', m[-1])
        return int(m[-1])
    
    # read xref table
    def read_xref_from(self, start, xrefs):
        """Reads XRefs from the given location."""
        self.setpos(start)
        self.reset()
        try:
            (pos, token) = self.nexttoken()
        except PSEOF:
            raise PDFNoValidXRef('Unexpected EOF')
        # logger.debug('read_xref_from: start=%d, token=%r', start, token)
        if isinstance(token, int):
            # XRefStream: PDF-1.5
            self.setpos(pos)
            self.reset()
            xref = PDFXRefStream()
            xref.load(self)
        else:
            if token is self.KEYWORD_XREF:
                self.nextline()
            xref = PDFXRef()
            xref.load(self)
        xrefs.append(xref)
        trailer = xref.get_trailer()
        logger.debug('trailer: %r', trailer)
        if 'XRefStm' in trailer:
            pos = int_value(trailer['XRefStm'])
            self.read_xref_from(pos, xrefs)
        if 'Prev' in trailer:
            # find previous xref
            pos = int_value(trailer['Prev'])
            self.read_xref_from(pos, xrefs)

    # read xref tables and trailers
    def read_xref(self):
        """Reads all the XRefs in the PDF file and returns them."""
        xrefs = []
        try:
            pos = self.find_xref()
            self.read_xref_from(pos, xrefs)
        except PDFNoValidXRef:
            # fallback
            logger.debug('no xref, fallback')
            self.fallback = True
            xref = PDFXRef()
            xref.load_fallback(self)
            xrefs.append(xref)
        return xrefs


class PDFStreamParser(PDFParser):

    """
    PDFStreamParser is used to parse PDF content streams
    that is contained in each page and has instructions
    for rendering the page. A reference to a PDF document is
    needed because a PDF content stream can also have
    indirect references to other objects in the same document.
    """

    def __init__(self, data):
        PDFParser.__init__(self, io.BytesIO(data))

    def flush(self):
        self.add_results(*self.popall())

    def do_keyword(self, pos, token):
        if token is self.KEYWORD_R:
            # reference to indirect object
            try:
                ((_,objid), (_,genno)) = self.pop(2)
                (objid, genno) = (int(objid), int(genno))
                obj = PDFObjRef(self.doc, objid, genno)
                self.push((pos, obj))
            except PSSyntaxError:
                pass
            return
        # others
        self.push((pos, token))
