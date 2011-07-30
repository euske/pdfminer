import sys
from .utils import mult_matrix, translate_matrix
from .utils import htmlescape, bbox2str
from .pdffont import PDFUnicodeNotDefined


class PDFDevice:

    def __init__(self, rsrcmgr):
        self.rsrcmgr = rsrcmgr
        self.ctm = None

    def __repr__(self):
        return '<PDFDevice>'

    def close(self):
        pass

    def set_ctm(self, ctm):
        self.ctm = ctm

    def begin_tag(self, tag, props=None):
        pass
    def end_tag(self):
        pass
    def do_tag(self, tag, props=None):
        pass

    def begin_page(self, page, ctm):
        pass
    def end_page(self, page):
        pass
    def begin_figure(self, name, bbox, matrix):
        pass
    def end_figure(self, name):
        pass

    def paint_path(self, graphicstate, stroke, fill, evenodd, path):
        pass
    def render_image(self, name, stream):
        pass
    def render_string(self, textstate, seq):
        pass


class PDFTextDevice(PDFDevice):

    def render_string(self, textstate, seq):
        matrix = mult_matrix(textstate.matrix, self.ctm)
        font = textstate.font
        fontsize = textstate.fontsize
        scaling = textstate.scaling * .01
        charspace = textstate.charspace * scaling
        wordspace = textstate.wordspace * scaling
        rise = textstate.rise
        if font.is_multibyte():
            wordspace = 0
        dxscale = .001 * fontsize * scaling
        if font.is_vertical():
            textstate.linematrix = self.render_string_vertical(
                seq, matrix, textstate.linematrix, font, fontsize,
                scaling, charspace, wordspace, rise, dxscale)
        else:
            textstate.linematrix = self.render_string_horizontal(
                seq, matrix, textstate.linematrix, font, fontsize,
                scaling, charspace, wordspace, rise, dxscale)
    
    def render_string_horizontal(self, seq, matrix, point, font, fontsize, scaling, charspace,
            wordspace, rise, dxscale):
        (x,y) = point
        needcharspace = False
        for obj in seq:
            if isinstance(obj, (int, float)):
                x -= obj*dxscale
                needcharspace = True
            else:
                for cid in font.decode(obj):
                    if needcharspace:
                        x += charspace
                    x += self.render_char(translate_matrix(matrix, (x,y)),
                                          font, fontsize, scaling, rise, cid)
                    if cid == 32 and wordspace:
                        x += wordspace
                    needcharspace = True
        return (x, y)

    def render_string_vertical(self, seq, matrix, point, font, fontsize, scaling, charspace,
            wordspace, rise, dxscale):
        (x,y) = point
        needcharspace = False
        for obj in seq:
            if isinstance(obj, (int, float)):
                y -= obj*dxscale
                needcharspace = True
            else:
                for cid in font.decode(obj):
                    if needcharspace:
                        y += charspace
                    y += self.render_char(translate_matrix(matrix, (x,y)), 
                                          font, fontsize, scaling, rise, cid)
                    if cid == 32 and wordspace:
                        y += wordspace
                    needcharspace = True
        return (x, y)

    def render_char(self, matrix, font, fontsize, scaling, rise, cid):
        return 0


class TagExtractor(PDFDevice):

    def __init__(self, rsrcmgr, outfp):
        PDFDevice.__init__(self, rsrcmgr)
        self.outfp = outfp
        self.pageno = 0
        self._stack = []

    def render_string(self, textstate, seq):
        font = textstate.font
        text = ''
        for obj in seq:
            if not isinstance(obj, str):
                continue
            chars = font.decode(obj)
            for cid in chars:
                try:
                    char = font.to_unichr(cid)
                    text += char
                except PDFUnicodeNotDefined:
                    pass
        self.outfp.write(htmlescape(text, self.outfp.encoding))

    def begin_page(self, page, ctm):
        self.outfp.write('<page id="%s" bbox="%s" rotate="%d">' %
                         (self.pageno, bbox2str(page.mediabox), page.rotate))

    def end_page(self, page):
        self.outfp.write('</page>\n')
        self.pageno += 1

    def begin_tag(self, tag, props=None):
        s = ''
        if isinstance(props, dict):
            s = ''.join( ' %s="%s"' % (htmlescape(k), htmlescape(str(v))) for (k,v)
                         in sorted(props.items()) )
        self.outfp.write('<%s%s>' % (htmlescape(tag.name), s))
        self._stack.append(tag)

    def end_tag(self):
        assert self._stack
        tag = self._stack.pop(-1)
        self.outfp.write('</%s>' % htmlescape(tag.name))

    def do_tag(self, tag, props=None):
        self.begin_tag(tag, props)
        self._stack.pop(-1)
