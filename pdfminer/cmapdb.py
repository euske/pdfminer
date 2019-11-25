#!/usr/bin/env python

""" Adobe character mapping (CMap) support.

CMaps provide the mapping between character codes and Unicode
code-points to character ids (CIDs).

More information is available on the Adobe website:

  http://opensource.adobe.com/wiki/display/cmap/CMap+Resources

"""

import sys
import os
import os.path
import gzip
import codecs
import marshal
import struct
import logging
from .psparser import PSStackParser
from .psparser import PSSyntaxError
from .psparser import PSEOF
from .psparser import PSLiteral
from .psparser import literal_name
from .psparser import KWD
from .encodingdb import name2unicode
from .utils import choplist
from .utils import nunpack


class CMapError(Exception):
    pass


##  CMapBase
##
class CMapBase:

    debug = 0

    def __init__(self, **kwargs):
        self.attrs = kwargs.copy()
        return

    def is_vertical(self):
        return self.attrs.get('WMode', 0) != 0

    def set_attr(self, k, v):
        self.attrs[k] = v
        return

    def add_code2cid(self, code, cid):
        return

    def add_cid2unichr(self, cid, code):
        return

    def use_cmap(self, cmap):
        return


##  CMap
##
class CMap(CMapBase):

    def __init__(self, **kwargs):
        CMapBase.__init__(self, **kwargs)
        self.code2cid = {}
        return

    def __repr__(self):
        return '<CMap: %s>' % self.attrs.get('CMapName')

    def use_cmap(self, cmap):
        assert isinstance(cmap, CMap)

        def copy(dst, src):
            for (k, v) in src.items():
                if isinstance(v, dict):
                    d = {}
                    dst[k] = d
                    copy(d, v)
                else:
                    dst[k] = v
        copy(self.code2cid, cmap.code2cid)
        return

    def decode(self, code):
        if self.debug:
            logging.debug('decode: %r, %r' % (self, code))
        d = self.code2cid
        for c in code:
            if c in d:
                d = d[c]
                if isinstance(d, int):
                    yield d
                    d = self.code2cid
            else:
                d = self.code2cid
        return

    def dump(self, out=sys.stdout, code2cid=None, code=None):
        if code2cid is None:
            code2cid = self.code2cid
            code = ()
        for (k, v) in sorted(code2cid.items()):
            c = code+(k,)
            if isinstance(v, int):
                out.write('code %r = cid %d\n' % (c, v))
            else:
                self.dump(out=out, code2cid=v, code=c)
        return


##  IdentityCMap
##
class IdentityCMap(CMapBase):

    def decode(self, code):
        n = len(code)//2
        if n:
            return struct.unpack('>%dH' % n, code)
        else:
            return ()


##  UnicodeMap
##
class UnicodeMap(CMapBase):

    def __init__(self, **kwargs):
        CMapBase.__init__(self, **kwargs)
        self.cid2unichr = {}
        return

    def __repr__(self):
        return '<UnicodeMap: %s>' % self.attrs.get('CMapName')

    def get_unichr(self, cid):
        if self.debug:
            logging.debug('get_unichr: %r, %r' % (self, cid))
        return self.cid2unichr[cid]

    def dump(self, out=sys.stdout):
        for (k, v) in sorted(self.cid2unichr.items()):
            out.write('cid %d = unicode %r\n' % (k, v))
        return


##  FileCMap
##
class FileCMap(CMap):

    def add_code2cid(self, code, cid):
        assert isinstance(code, bytes) and isinstance(cid, int)
        d = self.code2cid
        for c in code[:-1]:
            c = ord(c)
            if c in d:
                d = d[c]
            else:
                t = {}
                d[c] = t
                d = t
        c = ord(code[-1])
        d[c] = cid
        return


##  FileUnicodeMap
##
class FileUnicodeMap(UnicodeMap):

    def add_cid2unichr(self, cid, code):
        assert isinstance(cid, int)
        if isinstance(code, PSLiteral):
            # Interpret as an Adobe glyph name.
            self.cid2unichr[cid] = name2unicode(code.name)
        elif isinstance(code, bytes):
            # Interpret as UTF-16BE.
            self.cid2unichr[cid] = code.decode('UTF-16BE', 'ignore')
        elif isinstance(code, int):
            self.cid2unichr[cid] = chr(code)
        else:
            raise TypeError(code)
        return


##  PyCMap
##
class PyCMap(CMap):

    def __init__(self, name, module):
        CMap.__init__(self, CMapName=name)
        self.code2cid = module.CODE2CID
        if module.IS_VERTICAL:
            self.attrs['WMode'] = 1
        return


##  PyUnicodeMap
##
class PyUnicodeMap(UnicodeMap):

    def __init__(self, name, module, vertical):
        UnicodeMap.__init__(self, CMapName=name)
        if vertical:
            self.cid2unichr = module.CID2UNICHR_V
            self.attrs['WMode'] = 1
        else:
            self.cid2unichr = module.CID2UNICHR_H
        return


##  CMapDB
##
class CMapDB:

    _cmap_cache = {}
    _umap_cache = {}

    class CMapNotFound(CMapError):
        pass

    @classmethod
    def _load_data(klass, name):
        filename = '%s.marshal.gz' % name
        logging.info('loading: %r' % name)
        cmap_paths = (os.environ.get('CMAP_PATH', '/usr/share/pdfminer/'),
                      os.path.join(os.path.dirname(__file__), 'cmap'),)
        for directory in cmap_paths:
            path = os.path.join(directory, filename)
            if os.path.exists(path):
                gzfile = gzip.open(path)
                try:
                    return type(str(name), (), marshal.loads(gzfile.read()))
                finally:
                    gzfile.close()
        else:
            raise CMapDB.CMapNotFound(name)

    @classmethod
    def get_cmap(klass, name):
        if name == 'Identity-H':
            return IdentityCMap(WMode=0)
        elif name == 'Identity-V':
            return IdentityCMap(WMode=1)
        try:
            return klass._cmap_cache[name]
        except KeyError:
            pass
        data = klass._load_data(name)
        klass._cmap_cache[name] = cmap = PyCMap(name, data)
        return cmap

    @classmethod
    def get_unicode_map(klass, name, vertical=False):
        try:
            return klass._umap_cache[name][vertical]
        except KeyError:
            pass
        data = klass._load_data('to-unicode-%s' % name)
        klass._umap_cache[name] = umaps = [PyUnicodeMap(name, data, v) for v in (False, True)]
        return umaps[vertical]


##  CMapParser
##
class CMapParser(PSStackParser):

    def __init__(self, cmap, fp):
        PSStackParser.__init__(self, fp)
        self.cmap = cmap
        # some ToUnicode maps don't have "begincmap" keyword.
        self._in_cmap = True
        return

    def run(self):
        try:
            self.nextobject()
        except PSEOF:
            pass
        return

    KEYWORD_BEGINCMAP = KWD(b'begincmap')
    KEYWORD_ENDCMAP = KWD(b'endcmap')
    KEYWORD_USECMAP = KWD(b'usecmap')
    KEYWORD_DEF = KWD(b'def')
    KEYWORD_BEGINCODESPACERANGE = KWD(b'begincodespacerange')
    KEYWORD_ENDCODESPACERANGE = KWD(b'endcodespacerange')
    KEYWORD_BEGINCIDRANGE = KWD(b'begincidrange')
    KEYWORD_ENDCIDRANGE = KWD(b'endcidrange')
    KEYWORD_BEGINCIDCHAR = KWD(b'begincidchar')
    KEYWORD_ENDCIDCHAR = KWD(b'endcidchar')
    KEYWORD_BEGINBFRANGE = KWD(b'beginbfrange')
    KEYWORD_ENDBFRANGE = KWD(b'endbfrange')
    KEYWORD_BEGINBFCHAR = KWD(b'beginbfchar')
    KEYWORD_ENDBFCHAR = KWD(b'endbfchar')
    KEYWORD_BEGINNOTDEFRANGE = KWD(b'beginnotdefrange')
    KEYWORD_ENDNOTDEFRANGE = KWD(b'endnotdefrange')

    def do_keyword(self, pos, token):
        if token is self.KEYWORD_BEGINCMAP:
            self._in_cmap = True
            self.popall()
            return
        elif token is self.KEYWORD_ENDCMAP:
            self._in_cmap = False
            return
        if not self._in_cmap:
            return
        #
        if token is self.KEYWORD_DEF:
            try:
                ((_, k), (_, v)) = self.pop(2)
                self.cmap.set_attr(literal_name(k), v)
            except PSSyntaxError:
                pass
            return

        if token is self.KEYWORD_USECMAP:
            try:
                ((_, cmapname),) = self.pop(1)
                self.cmap.use_cmap(CMapDB.get_cmap(literal_name(cmapname)))
            except PSSyntaxError:
                pass
            except CMapDB.CMapNotFound:
                pass
            return

        if token is self.KEYWORD_BEGINCODESPACERANGE:
            self.popall()
            return
        if token is self.KEYWORD_ENDCODESPACERANGE:
            self.popall()
            return

        if token is self.KEYWORD_BEGINCIDRANGE:
            self.popall()
            return
        if token is self.KEYWORD_ENDCIDRANGE:
            objs = [obj for (__, obj) in self.popall()]
            for (s, e, cid) in choplist(3, objs):
                if (not isinstance(s, bytes) or not isinstance(e, bytes) or
                   not isinstance(cid, int) or len(s) != len(e)):
                    continue
                sprefix = s[:-4]
                eprefix = e[:-4]
                if sprefix != eprefix:
                    continue
                svar = s[-4:]
                evar = e[-4:]
                s1 = nunpack(svar)
                e1 = nunpack(evar)
                vlen = len(svar)
                #assert s1 <= e1
                for i in range(e1-s1+1):
                    x = sprefix+struct.pack('>L', s1+i)[-vlen:]
                    self.cmap.add_code2cid(x, cid+i)
            return

        if token is self.KEYWORD_BEGINCIDCHAR:
            self.popall()
            return
        if token is self.KEYWORD_ENDCIDCHAR:
            objs = [obj for (__, obj) in self.popall()]
            for (cid, code) in choplist(2, objs):
                if isinstance(code, bytes) and isinstance(cid, bytes):
                    self.cmap.add_code2cid(code, nunpack(cid))
            return

        if token is self.KEYWORD_BEGINBFRANGE:
            self.popall()
            return
        if token is self.KEYWORD_ENDBFRANGE:
            objs = [obj for (__, obj) in self.popall()]
            for (s, e, code) in choplist(3, objs):
                if (not isinstance(s, bytes) or not isinstance(e, bytes) or
                   len(s) != len(e)):
                        continue
                s1 = nunpack(s)
                e1 = nunpack(e)
                #assert s1 <= e1
                if isinstance(code, list):
                    for i in range(e1-s1+1):
                        self.cmap.add_cid2unichr(s1+i, code[i])
                else:
                    var = code[-4:]
                    base = nunpack(var)
                    prefix = code[:-4]
                    vlen = len(var)
                    for i in range(e1-s1+1):
                        x = prefix+struct.pack('>L', base+i)[-vlen:]
                        self.cmap.add_cid2unichr(s1+i, x)
            return

        if token is self.KEYWORD_BEGINBFCHAR:
            self.popall()
            return
        if token is self.KEYWORD_ENDBFCHAR:
            objs = [obj for (__, obj) in self.popall()]
            for (cid, code) in choplist(2, objs):
                if isinstance(cid, bytes) and isinstance(code, bytes):
                    self.cmap.add_cid2unichr(nunpack(cid), code)
            return

        if token is self.KEYWORD_BEGINNOTDEFRANGE:
            self.popall()
            return
        if token is self.KEYWORD_ENDNOTDEFRANGE:
            self.popall()
            return

        self.push((pos, token))
        return


##  CMapConverter
##
class CMapConverter:

    def __init__(self, enc2codec={}):
        self.enc2codec = enc2codec
        self.code2cid = {} # {'cmapname': ...}
        self.is_vertical = {}
        self.cid2unichr_h = {} # {cid: unichr}
        self.cid2unichr_v = {} # {cid: unichr}
        return

    def get_encs(self):
        return self.code2cid.keys()

    def get_maps(self, enc):
        if enc.endswith('-H'):
            (hmapenc, vmapenc) = (enc, None)
        elif enc == 'H':
            (hmapenc, vmapenc) = ('H', 'V')
        else:
            (hmapenc, vmapenc) = (enc+'-H', enc+'-V')
        if hmapenc in self.code2cid:
            hmap = self.code2cid[hmapenc]
        else:
            hmap = {}
            self.code2cid[hmapenc] = hmap
        vmap = None
        if vmapenc:
            self.is_vertical[vmapenc] = True
            if vmapenc in self.code2cid:
                vmap = self.code2cid[vmapenc]
            else:
                vmap = {}
                self.code2cid[vmapenc] = vmap
        return (hmap, vmap)

    def load(self, fp):
        encs = None
        for line in fp:
            (line,_,_) = line.strip().partition('#')
            if not line: continue
            values = line.split('\t')
            if encs is None:
                assert values[0] == 'CID'
                encs = values
                continue

            def put(dmap, code, cid, force=False):
                for b in code[:-1]:
                    if b in dmap:
                        dmap = dmap[b]
                    else:
                        d = {}
                        dmap[b] = d
                        dmap = d
                b = code[-1]
                if force or ((b not in dmap) or dmap[b] == cid):
                    dmap[b] = cid
                return

            def add(unimap, enc, code):
                try:
                    codec = self.enc2codec[enc]
                    c = code.decode(codec, 'strict')
                    if len(c) == 1:
                        if c not in unimap:
                            unimap[c] = 0
                        unimap[c] += 1
                except KeyError:
                    pass
                except UnicodeError:
                    pass
                return

            def pick(unimap):
                chars = sorted(
                    unimap.items(),
                    key=(lambda x:(x[1],-ord(x[0]))), reverse=True)
                (c,_) = chars[0]
                return c

            cid = int(values[0])
            unimap_h = {}
            unimap_v = {}
            for (enc,value) in zip(encs, values):
                if enc == 'CID': continue
                if value == '*': continue

                # hcodes, vcodes: encoded bytes for each writing mode.
                hcodes = []
                vcodes = []
                for code in value.split(','):
                    vertical = code.endswith('v')
                    if vertical:
                        code = code[:-1]
                    try:
                        code = codecs.decode(code, 'hex')
                    except:
                        code = bytes([int(code, 16)])
                    if vertical:
                        vcodes.append(code)
                        add(unimap_v, enc, code)
                    else:
                        hcodes.append(code)
                        add(unimap_h, enc, code)
                # add cid to each map.
                (hmap, vmap) = self.get_maps(enc)
                if vcodes:
                    assert vmap is not None
                    for code in vcodes:
                        put(vmap, code, cid, True)
                    for code in hcodes:
                        put(hmap, code, cid, True)
                else:
                    for code in hcodes:
                        put(hmap, code, cid)
                        put(vmap, code, cid)

            # Determine the "most popular" candidate.
            if unimap_h:
                self.cid2unichr_h[cid] = pick(unimap_h)
            if unimap_v or unimap_h:
                self.cid2unichr_v[cid] = pick(unimap_v or unimap_h)

        return

    def dump_cmap(self, fp, enc):
        data = dict(
            IS_VERTICAL=self.is_vertical.get(enc, False),
            CODE2CID=self.code2cid.get(enc),
        )
        fp.write(marshal.dumps(data))
        return

    def dump_unicodemap(self, fp):
        data = dict(
            CID2UNICHR_H=self.cid2unichr_h,
            CID2UNICHR_V=self.cid2unichr_v,
        )
        fp.write(marshal.dumps(data))
        return

# convert_cmap
def convert_cmap(outdir, regname, enc2codec, paths):
    converter = CMapConverter(enc2codec)

    for path in paths:
        print('reading: %r...' % path)
        with open(path) as fp:
            converter.load(fp)

    files = []
    for enc in converter.get_encs():
        fname = '%s.marshal.gz' % enc
        path = os.path.join(outdir, fname)
        print('writing: %r...' % path)
        with gzip.open(path, 'wb') as fp:
            converter.dump_cmap(fp, enc)
        files.append(path)

    fname = 'to-unicode-%s.marshal.gz' % regname
    path = os.path.join(outdir, fname)
    print('writing: %r...' % path)
    with gzip.open(path, 'wb') as fp:
        converter.dump_unicodemap(fp)
    files.append(path)
    return files


# test
def main(argv):
    args = argv[1:]
    for fname in args:
        with open(fname, 'rb') as fp:
            cmap = FileUnicodeMap()
            #cmap = FileCMap()
            CMapParser(cmap, fp).run()
            cmap.dump()
    return

if __name__ == '__main__':
    sys.exit(main(sys.argv))
