#!/usr/bin/env python
import logging
import re
from .pdfdevice import PDFTextDevice
from .pdffont import PDFUnicodeNotDefined
from .layout import LTContainer
from .layout import LTPage
from .layout import LTText
from .layout import LTLine
from .layout import LTRect
from .layout import LTCurve
from .layout import LTFigure
from .layout import LTImage
from .layout import LTChar
from .layout import LTTextLine
from .layout import LTTextBox
from .layout import LTTextBoxVertical
from .layout import LTTextGroup
from .utils import apply_matrix_pt
from .utils import mult_matrix
from .utils import enc
from .utils import bbox2str


##  PDFLayoutAnalyzer
##
class PDFLayoutAnalyzer(PDFTextDevice):

    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFTextDevice.__init__(self, rsrcmgr)
        self.pageno = pageno
        self.laparams = laparams
        self._stack = []
        return

    def begin_page(self, page, ctm):
        (x0, y0, x1, y1) = page.mediabox
        (x0, y0) = apply_matrix_pt(ctm, (x0, y0))
        (x1, y1) = apply_matrix_pt(ctm, (x1, y1))
        mediabox = (0, 0, abs(x0-x1), abs(y0-y1))
        self.cur_item = LTPage(self.pageno, mediabox)
        return

    def end_page(self, page):
        assert not self._stack
        assert isinstance(self.cur_item, LTPage)
        if self.laparams is not None:
            self.cur_item.analyze(self.laparams)
        self.pageno += 1
        self.receive_layout(self.cur_item)
        return

    def begin_figure(self, name, bbox, matrix):
        self._stack.append(self.cur_item)
        self.cur_item = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
        return

    def end_figure(self, _):
        fig = self.cur_item
        assert isinstance(self.cur_item, LTFigure)
        self.cur_item = self._stack.pop()
        self.cur_item.add(fig)
        return

    def render_image(self, name, stream):
        assert isinstance(self.cur_item, LTFigure)
        item = LTImage(name, stream,
                       (self.cur_item.x0, self.cur_item.y0,
                        self.cur_item.x1, self.cur_item.y1))
        self.cur_item.add(item)
        return

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        shape = ''.join(x[0] for x in path)
        if shape == 'ml':
            # horizontal/vertical line
            (_, x0, y0) = path[0]
            (_, x1, y1) = path[1]
            (x0, y0) = apply_matrix_pt(self.ctm, (x0, y0))
            (x1, y1) = apply_matrix_pt(self.ctm, (x1, y1))
            if x0 == x1 or y0 == y1:
                self.cur_item.add(LTLine(gstate.linewidth, (x0, y0), (x1, y1)))
                return
        if shape == 'mlllh':
            # rectangle
            (_, x0, y0) = path[0]
            (_, x1, y1) = path[1]
            (_, x2, y2) = path[2]
            (_, x3, y3) = path[3]
            (x0, y0) = apply_matrix_pt(self.ctm, (x0, y0))
            (x1, y1) = apply_matrix_pt(self.ctm, (x1, y1))
            (x2, y2) = apply_matrix_pt(self.ctm, (x2, y2))
            (x3, y3) = apply_matrix_pt(self.ctm, (x3, y3))
            if ((x0 == x1 and y1 == y2 and x2 == x3 and y3 == y0) or
                (y0 == y1 and x1 == x2 and y2 == y3 and x3 == x0)):
                self.cur_item.add(LTRect(gstate.linewidth, (x0, y0, x2, y2)))
                return
        # other shapes
        pts = []
        for p in path:
            for i in xrange(1, len(p), 2):
                pts.append(apply_matrix_pt(self.ctm, (p[i], p[i+1])))
        self.cur_item.add(LTCurve(gstate.linewidth, pts))
        return

    def render_char(self, matrix, font, fontsize, scaling, rise, cid):
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, unicode), text
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTChar(matrix, font, fontsize, scaling, rise, text, textwidth, textdisp)
        self.cur_item.add(item)
        return item.adv

    def handle_undefined_char(self, font, cid):
        logging.info('undefined: %r, %r' % (font, cid))
        return '(cid:%d)' % cid

    def receive_layout(self, ltpage):
        return


##  PDFPageAggregator
##
class PDFPageAggregator(PDFLayoutAnalyzer):

    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFLayoutAnalyzer.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)
        self.result = None
        return

    def receive_layout(self, ltpage):
        self.result = ltpage
        return

    def get_result(self):
        return self.result


##  PDFConverter
##
class PDFConverter(PDFLayoutAnalyzer):

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None):
        PDFLayoutAnalyzer.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)
        self.outfp = outfp
        self.codec = codec
        return


##  TextConverter
##
class TextConverter(PDFConverter):

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 showpageno=False, imagewriter=None):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.showpageno = showpageno
        self.imagewriter = imagewriter
        return

    def write_text(self, text):
        self.outfp.write(text.encode(self.codec, 'ignore'))
        return

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTText):
                self.write_text(item.get_text())
            if isinstance(item, LTTextBox):
                self.write_text('\n')
            elif isinstance(item, LTImage):
                if self.imagewriter is not None:
                    self.imagewriter.export_image(item)
        if self.showpageno:
            self.write_text('Page %s\n' % ltpage.pageid)
        render(ltpage)
        self.write_text('\f')
        return

    # Some dummy functions to save memory/CPU when all that is wanted
    # is text.  This stops all the image and drawing ouput from being
    # recorded and taking up RAM.
    def render_image(self, name, stream):
        if self.imagewriter is None:
            return
        PDFConverter.render_image(self, name, stream)
        return

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        return


##  HTMLConverter
##
class HTMLConverter(PDFConverter):

    RECT_COLORS = {
        #'char': 'green',
        'figure': 'yellow',
        'textline': 'magenta',
        'textbox': 'cyan',
        'textgroup': 'red',
        'curve': 'black',
        'page': 'gray',
    }

    TEXT_COLORS = {
        'textbox': 'blue',
        'char': 'black',
    }

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 scale=1, fontscale=1.0, layoutmode='normal', showpageno=True,
                 pagemargin=50, imagewriter=None, debug=0,
                 rect_colors={'curve': 'black', 'page': 'gray'},
                 text_colors={'char': 'black'}):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.scale = scale
        self.fontscale = fontscale
        self.layoutmode = layoutmode
        self.showpageno = showpageno
        self.pagemargin = pagemargin
        self.imagewriter = imagewriter
        self.rect_colors = rect_colors
        self.text_colors = text_colors
        if debug:
            self.rect_colors.update(self.RECT_COLORS)
            self.text_colors.update(self.TEXT_COLORS)
        self._yoffset = self.pagemargin
        self._font = None
        self._fontstack = []
        self.write_header()
        return

    def write(self, text):
        self.outfp.write(text)
        return

    def write_header(self):
        self.write('<html><head>\n')
        self.write('<meta http-equiv="Content-Type" content="text/html; charset=%s">\n' % self.codec)
        self.write('</head><body>\n')
        return

    def write_footer(self):
        self.write('<div style="position:absolute; top:0px;">Page: %s</div>\n' %
                   ', '.join('<a href="#%s">%s</a>' % (i, i) for i in xrange(1, self.pageno)))
        self.write('</body></html>\n')
        return

    def write_text(self, text):
        self.write(enc(text, self.codec))
        return

    def place_rect(self, color, borderwidth, x, y, w, h):
        color = self.rect_colors.get(color)
        if color is not None:
            self.write('<span style="position:absolute; border: %s %dpx solid; '
                       'left:%dpx; top:%dpx; width:%dpx; height:%dpx;"></span>\n' %
                       (color, borderwidth,
                        x*self.scale, (self._yoffset-y)*self.scale,
                        w*self.scale, h*self.scale))
        return

    def place_border(self, color, borderwidth, item):
        self.place_rect(color, borderwidth, item.x0, item.y1, item.width, item.height)
        return

    def place_image(self, item, borderwidth, x, y, w, h):
        if self.imagewriter is not None:
            name = self.imagewriter.export_image(item)
            self.write('<img src="%s" border="%d" style="position:absolute; left:%dpx; top:%dpx;" '
                       'width="%d" height="%d" />\n' %
                       (enc(name), borderwidth,
                        x*self.scale, (self._yoffset-y)*self.scale,
                        w*self.scale, h*self.scale))
        return

    def place_text(self, color, text, x, y, size):
        color = self.text_colors.get(color)
        if color is not None:
            self.write('<span style="position:absolute; color:%s; left:%dpx; top:%dpx; font-size:%dpx;">' %
                       (color, x*self.scale, (self._yoffset-y)*self.scale, size*self.scale*self.fontscale))
            self.write_text(text)
            self.write('</span>\n')
        return

    def begin_div(self, color, borderwidth, x, y, w, h, writing_mode=False):
        self._fontstack.append(self._font)
        self._font = None
        self.write('<div style="position:absolute; border: %s %dpx solid; writing-mode:%s; '
                   'left:%dpx; top:%dpx; width:%dpx; height:%dpx;">' %
                   (color, borderwidth, writing_mode,
                    x*self.scale, (self._yoffset-y)*self.scale,
                    w*self.scale, h*self.scale))
        return

    def end_div(self, color):
        if self._font is not None:
            self.write('</span>')
        self._font = self._fontstack.pop()
        self.write('</div>')
        return

    def put_text(self, text, fontname, fontsize):
        font = (fontname, fontsize)
        if font != self._font:
            if self._font is not None:
                self.write('</span>')
            self.write('<span style="font-family: %s; font-size:%dpx">' %
                       (enc(fontname), fontsize * self.scale * self.fontscale))
            self._font = font
        self.write_text(text)
        return

    def put_newline(self):
        self.write('<br>')
        return

    def receive_layout(self, ltpage):
        def show_group(item):
            if isinstance(item, LTTextGroup):
                self.place_border('textgroup', 1, item)
                for child in item:
                    show_group(child)
            return

        def render(item):
            if isinstance(item, LTPage):
                self._yoffset += item.y1
                self.place_border('page', 1, item)
                if self.showpageno:
                    self.write('<div style="position:absolute; top:%dpx;">' %
                               ((self._yoffset-item.y1)*self.scale))
                    self.write('<a name="%s">Page %s</a></div>\n' % (item.pageid, item.pageid))
                for child in item:
                    render(child)
                if item.groups is not None:
                    for group in item.groups:
                        show_group(group)
            elif isinstance(item, LTCurve):
                self.place_border('curve', 1, item)
            elif isinstance(item, LTFigure):
                self.begin_div('figure', 1, item.x0, item.y1, item.width, item.height)
                for child in item:
                    render(child)
                self.end_div('figure')
            elif isinstance(item, LTImage):
                self.place_image(item, 1, item.x0, item.y1, item.width, item.height)
            else:
                if self.layoutmode == 'exact':
                    if isinstance(item, LTTextLine):
                        self.place_border('textline', 1, item)
                        for child in item:
                            render(child)
                    elif isinstance(item, LTTextBox):
                        self.place_border('textbox', 1, item)
                        self.place_text('textbox', str(item.index+1), item.x0, item.y1, 20)
                        for child in item:
                            render(child)
                    elif isinstance(item, LTChar):
                        self.place_border('char', 1, item)
                        self.place_text('char', item.get_text(), item.x0, item.y1, item.size)
                else:
                    if isinstance(item, LTTextLine):
                        for child in item:
                            render(child)
                        if self.layoutmode != 'loose':
                            self.put_newline()
                    elif isinstance(item, LTTextBox):
                        self.begin_div('textbox', 1, item.x0, item.y1, item.width, item.height,
                                       item.get_writing_mode())
                        for child in item:
                            render(child)
                        self.end_div('textbox')
                    elif isinstance(item, LTChar):
                        self.put_text(item.get_text(), item.fontname, item.size)
                    elif isinstance(item, LTText):
                        self.write_text(item.get_text())
            return
        render(ltpage)
        self._yoffset += self.pagemargin
        return

    def close(self):
        self.write_footer()
        return


##  XMLConverter
##
class XMLConverter(PDFConverter):

    CONTROL = re.compile(ur'[\x00-\x08\x0b-\x0c\x0e-\x1f]')

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1,
                 laparams=None, imagewriter=None, stripcontrol=False):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.imagewriter = imagewriter
        self.stripcontrol = stripcontrol
        self.write_header()
        return

    def write_header(self):
        self.outfp.write('<?xml version="1.0" encoding="%s" ?>\n' % self.codec)
        self.outfp.write('<pages>\n')
        return

    def write_footer(self):
        self.outfp.write('</pages>\n')
        return

    def write_text(self, text):
        if self.stripcontrol:
            text = self.CONTROL.sub(u'', text)
        self.outfp.write(enc(text, self.codec))
        return

    def receive_layout(self, ltpage):
        def show_group(item):
            if isinstance(item, LTTextBox):
                self.outfp.write('<textbox id="%d" bbox="%s" />\n' %
                                 (item.index, bbox2str(item.bbox)))
            elif isinstance(item, LTTextGroup):
                self.outfp.write('<textgroup bbox="%s">\n' % bbox2str(item.bbox))
                for child in item:
                    show_group(child)
                self.outfp.write('</textgroup>\n')
            return

        def render(item):
            if isinstance(item, LTPage):
                self.outfp.write('<page id="%s" bbox="%s" rotate="%d">\n' %
                                 (item.pageid, bbox2str(item.bbox), item.rotate))
                for child in item:
                    render(child)
                if item.groups is not None:
                    self.outfp.write('<layout>\n')
                    for group in item.groups:
                        show_group(group)
                    self.outfp.write('</layout>\n')
                self.outfp.write('</page>\n')
            elif isinstance(item, LTLine):
                self.outfp.write('<line linewidth="%d" bbox="%s" />\n' %
                                 (item.linewidth, bbox2str(item.bbox)))
            elif isinstance(item, LTRect):
                self.outfp.write('<rect linewidth="%d" bbox="%s" />\n' %
                                 (item.linewidth, bbox2str(item.bbox)))
            elif isinstance(item, LTCurve):
                self.outfp.write('<curve linewidth="%d" bbox="%s" pts="%s"/>\n' %
                                 (item.linewidth, bbox2str(item.bbox), item.get_pts()))
            elif isinstance(item, LTFigure):
                self.outfp.write('<figure name="%s" bbox="%s">\n' %
                                 (item.name, bbox2str(item.bbox)))
                for child in item:
                    render(child)
                self.outfp.write('</figure>\n')
            elif isinstance(item, LTTextLine):
                self.outfp.write('<textline bbox="%s">\n' % bbox2str(item.bbox))
                for child in item:
                    render(child)
                self.outfp.write('</textline>\n')
            elif isinstance(item, LTTextBox):
                wmode = ''
                if isinstance(item, LTTextBoxVertical):
                    wmode = ' wmode="vertical"'
                self.outfp.write('<textbox id="%d" bbox="%s"%s>\n' %
                                 (item.index, bbox2str(item.bbox), wmode))
                for child in item:
                    render(child)
                self.outfp.write('</textbox>\n')
            elif isinstance(item, LTChar):
                self.outfp.write('<text font="%s" bbox="%s" size="%.3f">' %
                                 (enc(item.fontname), bbox2str(item.bbox), item.size))
                self.write_text(item.get_text())
                self.outfp.write('</text>\n')
            elif isinstance(item, LTText):
                self.outfp.write('<text>%s</text>\n' % item.get_text())
            elif isinstance(item, LTImage):
                if self.imagewriter is not None:
                    name = self.imagewriter.export_image(item)
                    self.outfp.write('<image src="%s" width="%d" height="%d" />\n' %
                                     (enc(name), item.width, item.height))
                else:
                    self.outfp.write('<image width="%d" height="%d" />\n' %
                                     (item.width, item.height))
            else:
                assert 0, item
            return
        render(ltpage)
        return

    def close(self):
        self.write_footer()
        return


##  XMLAltoConverter
##
## TODO Manage hyphenations (in a second step with all pages).
##
class XMLAltoConverter(PDFConverter):

    CONTROL = re.compile(u'[\x00-\x08\x0b-\x0c\x0e-\x1f]')

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1,
                 laparams=None, imagewriter=None, stripcontrol=False):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.imagewriter = imagewriter
        self.stripcontrol = stripcontrol
        self.write_header()
        return

    def write(self, text):
        if self.codec:
            text = text.encode(self.codec)
        self.outfp.write(text)
        return

    def write_header(self):
        if self.codec:
            self.write('<?xml version="1.0" encoding="%s" ?>\n' % self.codec)
        else:
            self.write('<?xml version="1.0" ?>\n')
        # TODO Add ID="alto.0000004" from filename without extension.
        self.write('<alto xmlns="http://www.loc.gov/standards/alto/ns-v3#" xmlns:xlink="http://www.w3.org/TR/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/standards/alto/ns-v3# https://www.loc.gov/standards/alto/v3/alto.xsd" SCHEMAVERSION="3.1">\n')
        self.div_description()
        # self.div_styles()
        # self.div_tags()
        self.write('<Layout>\n')
        return

    def write_footer(self):
        self.write('</Layout>\n')
        self.write('</alto>\n')
        return

    def write_text(self, text):
        if self.stripcontrol:
            text = self.CONTROL.sub(u'', text)
        self.write(text)
        return

    def div_description(self):
        # TODO Convert into millimeters.
        self.write('<Description>\n')
        self.write('<MeasurementUnit>pixel</MeasurementUnit>\n')
        # TODO Get filepath
        # self.write('<sourceImageInformation>\n')
        # self.write('<fileName>%s</fileName>\n' % ('filename.pdf'))
        # self.write('</sourceImageInformation>\n')
        # TODO Add more description if available in source.
        self.write('</Description>\n')
        return

    def div_styles(self):
        # TODO List of fonts for texts and paragraphs.
        # self.write('<Styles>\n')
        # self.write('</Styles>\n')
        return

    def div_tags(self):
        # TODO List of tags.
        # self.write('<Tags>\n')
        # self.write('</Tags>\n')
        return

    def receive_layout(self, ltpage):
        def render(item):
            def begin_page(item):
                self.write('<Page ID="PAG_%d" HEIGHT="%s" WIDTH="%s" PHYSICAL_IMG_NR="%d">\n' %
                           (item.pageid,
                            item.height, item.width,
                            item.pageid))
                return

            def begin_printspace(item):
                self.write('<PrintSpace ID="PAG_%d_PrintSpace" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s">\n' %
                           (item.pageid,
                            item.height, item.width,
                            0, 0))
                return

            def begin_composedblock(item):
                self._index_composedblock += 1
                self.write('<ComposedBlock ID="PAG_%d_CB_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s">\n' %
                           (ltpage.pageid, self._index_composedblock,
                            item.height, item.width,
                            item.x0, ltpage.height - item.y0))
                return

            def begin_textblock(item):
                self._index_textblock += 1
                self.write('<TextBlock ID="PAG_%d_TB_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s">\n' %
                           (ltpage.pageid, self._index_textblock,
                            item.height, item.width,
                            item.x0, ltpage.height - item.y0))
                return

            def begin_textline(item):
                self._index_textline += 1
                self.write('<TextLine ID="PAG_%d_TL_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s">\n' %
                           (ltpage.pageid, self._index_textline,
                            item.height, item.width,
                            item.x0, ltpage.height - item.y0))
                return

            def write_illustration(item, name = ''):
                self._index_illustration += 1
                if name:
                    name = 'FILEID=%s ' % enc(name, None)
                self.write('<Illustration ID="PAG_%d_IL_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s" %s/>\n' %
                           (ltpage.pageid, self._index_illustration,
                            item.height, item.width,
                            item.x0, ltpage.height - item.y0,
                            name))
                return

            def write_graphicalelement(item):
                self._index_graphicalelement += 1
                self.write('<GraphicalElement ID="PAG_%d_GE_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s" />\n' %
                           (ltpage.pageid, self._index_graphicalelement,
                            item.height, item.width,
                            item.x0, ltpage.height - item.y0))
                return

            def end_xmltag(xmltag):
                self.write('</' + xmltag + '>\n')
                return

            def write_string(width, height, x, y, content):
                self._index_string += 1
                self.write('<String ID="PAG_%d_ST_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s" CONTENT="' %
                           (ltpage.pageid, self._index_string,
                            height, width,
                            x, y))
                self.write_text(content)
                self.write('" />\n')
                return

            def write_space(width, height, x, y):
                self._index_space += 1
                self.write('<SP ID="PAG_%d_SP_%d" HEIGHT="%s" WIDTH="%s" HPOS="%s" VPOS="%s" />\n' %
                           (ltpage.pageid, self._index_space,
                            height, width,
                            x, y))
                return

            def write_shape(item):
                self.write('<Shape>\n')
                self.write('<Polygon POINTS="%s" />\n' % item.get_pts())
                self.write('</Shape>\n')
                return

            if isinstance(item, LTPage):
                self._index_composedblock = 0
                self._index_textblock = 0
                self._index_textline = 0
                self._index_string = 0
                self._index_space = 0
                self._index_illustration = 0
                self._index_graphicalelement = 0
                self._textblock_vertical = False
                # TODO Add the printed page number (PRINTED_IMG_NR), etc.
                begin_page(item)
                # TODO Identify margins and print space.
                # PrintSpace is required when there is no margin.
                # <TopMargin/>
                # <LeftMargin/>
                # <RightMargin/>
                # <BottomMargin/>
                begin_printspace(item)
                # TODO Add an option to create composed blocks.
                #if (item.groups is not None) and layoutmode == medium:
                #    for group in item.groups:
                #        render(group)
                #else:
                for child in item:
                    render(child)
                end_xmltag('PrintSpace')
                end_xmltag('Page')
            elif isinstance(item, LTTextGroup):
                begin_composedblock(item)
                for child in item:
                    render(child)
                end_xmltag('ComposedBlock')
            elif isinstance(item, LTTextBox):
                # NOTE With text with non-standard spaces, the text boxes and
                # the text lines may be wider than the width for words, because
                # words contains the excedent space. So, the size of the text
                # box and the text lines should be computed without the last
                # space of each word. This is not done currently, because these
                # text are rare.
                self._textblock_vertical = isinstance(item, LTTextBoxVertical)
                # The textbox contains the next space, except the last on the line.
                begin_textblock(item)
                for child in item:
                    render(child)
                end_xmltag('TextBlock')
            elif isinstance(item, LTTextLine):
                begin_textline(item)
                # A line contain characters, but only words and spaces are
                # managed in Alto, so the words are rebuilt.
                words = []
                word = []
                prev_character = ''
                for child in item:
                    character = child.get_text()
                    if isinstance(child, LTChar):
                        if word:
                            if character != ' ':
                                if prev_character == ' ':
                                    words.append(word)
                                    word = []
                            else:
                                if prev_character != ' ':
                                    words.append(word)
                                    word = []
                        word.append(child)
                    elif word and prev_character != ' ':
                        words.append(word)
                        word = []
                    prev_character = character
                # Print each string (word or space).
                prev_word = False
                for word in words:
                    x0, x1, y0, y1 = [], [], [], []
                    content = ''
                    for character in word:
                        x0.append(character.x0)
                        x1.append(character.x1)
                        y0.append(character.y0)
                        y1.append(character.y1)
                        content += character.get_text()
                    if content[0] != ' ':
                        # The required space between two words may be missing
                        # according to the parameter "word margin", so it may be
                        # added.
                        if prev_word:
                            if self._textblock_vertical:
                                write_space(word_y1 - min(y0), word_width,
                                            word_x0, ltpage.height - word_y1)
                            else:
                                write_space(word_height, min(x0) - word_x1,
                                            word_x1, ltpage.height - word_y0)
                        # Remember and write the string for next missing space.
                        word_x0 = min(x0)
                        word_x1 = max(x1)
                        word_width = word_x1 - word_x0
                        word_y0 = min(y0)
                        word_y1 = max(y1)
                        word_height = word_y1 - word_y0
                        prev_word = True
                        write_string(word_width, word_height,
                                     word_x0, ltpage.height - word_y0,
                                     content)
                    else:
                        word_x0 = min(x0)
                        word_x1 = max(x1)
                        word_width = word_x1 - word_x0
                        word_y0 = min(y0)
                        word_y1 = max(y1)
                        word_height = word_y1 - word_y0
                        prev_word = False
                        write_space(word_width, word_height,
                                    word_x0, ltpage.height - word_y0)
                end_xmltag('TextLine')
            elif isinstance(item, LTFigure):
                for child in item:
                    if isinstance(child, LTImage):
                        render(child)
                    else:
                        begin_composedblock(item)
                        render(child)
                        end_xmltag('ComposedBlock')
            elif isinstance(item, LTImage):
                if self.imagewriter is not None:
                    name = self.imagewriter.export_image(item)
                else:
                    name = ''
                write_illustration(item, name)
            elif isinstance(item, LTLine):
                write_graphicalelement(item)
            elif isinstance(item, LTRect):
                write_graphicalelement(item)
            elif isinstance(item, LTCurve):
                write_shape(item)
            else:
                assert 0, item
            return
        render(ltpage)
        return

    def close(self):
        self.write_footer()
        return
