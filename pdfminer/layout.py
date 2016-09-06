import logging
from itertools import combinations

from .utils import (INF, get_bound, uniq, fsplit, drange, bbox2str, matrix2str, apply_matrix_pt,
    trailiter)


logger = logging.getLogger(__name__)


class IndexAssigner:

    def __init__(self, index=0):
        self.index = index

    def run(self, obj):
        if isinstance(obj, LTTextBox):
            obj.index = self.index
            self.index += 1
        elif isinstance(obj, LTTextGroup):
            for x in obj:
                self.run(x)


class LAParams:

    def __init__(self, line_overlap=0.5, char_margin=2.0, line_margin=0.5, word_margin=0.1,
            boxes_flow=0.5, detect_vertical=False, all_texts=False, paragraph_indent=None,
            heuristic_word_margin=False):
        self.line_overlap = line_overlap
        self.char_margin = char_margin
        self.line_margin = line_margin
        self.word_margin = word_margin
        self.boxes_flow = boxes_flow
        self.detect_vertical = detect_vertical
        self.all_texts = all_texts
        # If this setting is not None, horizontal text boxes will be split by paragraphs, using
        # the indent of their first line for the split. The numerical argument is the treshold that
        # the line's x-pos must reach to be considered "indented".
        self.paragraph_indent = paragraph_indent
        # In many cases, the whole word_margin mechanism is useless because space characters are
        # already included in the text. In fact, it's even harmful because it sometimes causes
        # spurious space characters to be inserted. when heuristic_word_margin is enabled, text
        # lines already containing space characters will have their word margin multiplied by 5 to
        # avoid this spurious space problem. We don't skip space insertion altogether because it's
        # possible that a layout peculiarity causes a big space not to contain the space character
        # itself, and we want to count those.
        self.heuristic_word_margin = heuristic_word_margin

    def __repr__(self):
        return ('<LAParams: char_margin=%.1f, line_margin=%.1f, word_margin=%.1f all_texts=%r>' %
                (self.char_margin, self.line_margin, self.word_margin, self.all_texts))


class LTItem:

    def analyze(self, laparams):
        """Perform the layout analysis."""


class LTText:

    def __repr__(self):
        return ('<%s %r>' %
                (self.__class__.__name__, self.get_text()))

    def get_text(self):
        raise NotImplementedError


class LTComponent(LTItem):

    def __init__(self, bbox):
        LTItem.__init__(self)
        self.set_bbox(bbox)

    def __repr__(self):
        return ('<%s %s>' % (self.__class__.__name__, bbox2str(self.bbox)))

    def set_bbox(self, bbox):
        (x0,y0,x1,y1) = bbox
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.width = x1-x0
        self.height = y1-y0
        self.bbox = (x0, y0, x1, y1)

    def is_empty(self):
        return self.width <= 0 or self.height <= 0
        
    def is_hoverlap(self, obj):
        assert isinstance(obj, LTComponent)
        return obj.x0 <= self.x1 and self.x0 <= obj.x1

    def hdistance(self, obj):
        assert isinstance(obj, LTComponent)
        if self.is_hoverlap(obj):
            return 0
        else:
            return min(abs(self.x0-obj.x1), abs(self.x1-obj.x0))

    def hoverlap(self, obj):
        assert isinstance(obj, LTComponent)
        if self.is_hoverlap(obj):
            return min(abs(self.x0-obj.x1), abs(self.x1-obj.x0))
        else:
            return 0

    def is_voverlap(self, obj):
        assert isinstance(obj, LTComponent)
        return obj.y0 <= self.y1 and self.y0 <= obj.y1

    def vdistance(self, obj):
        assert isinstance(obj, LTComponent)
        if self.is_voverlap(obj):
            return 0
        else:
            return min(abs(self.y0-obj.y1), abs(self.y1-obj.y0))

    def voverlap(self, obj):
        assert isinstance(obj, LTComponent)
        if self.is_voverlap(obj):
            return min(abs(self.y0-obj.y1), abs(self.y1-obj.y0))
        else:
            return 0


class LTCurve(LTComponent):

    def __init__(self, linewidth, pts):
        LTComponent.__init__(self, get_bound(pts))
        self.pts = pts
        self.linewidth = linewidth

    def get_pts(self):
        return ','.join( '%.3f,%.3f' % p for p in self.pts )


class LTLine(LTCurve):

    def __init__(self, linewidth, p0, p1):
        LTCurve.__init__(self, linewidth, [p0, p1])


class LTRect(LTCurve):

    def __init__(self, linewidth, rect):
        (x0,y0,x1,y1) = rect
        LTCurve.__init__(self, linewidth, [(x0,y0), (x1,y0), (x1,y1), (x0,y1)])


class LTImage(LTComponent):

    def __init__(self, name, stream, bbox):
        LTComponent.__init__(self, bbox)
        self.name = name
        self.stream = stream
        self.srcsize = (stream.get_any(('W', 'Width')),
                        stream.get_any(('H', 'Height')))
        self.imagemask = stream.get_any(('IM', 'ImageMask'))
        self.bits = stream.get_any(('BPC', 'BitsPerComponent'), 1)
        self.colorspace = stream.get_any(('CS', 'ColorSpace'))
        if not isinstance(self.colorspace, list):
            self.colorspace = [self.colorspace]

    def __repr__(self):
        return ('<%s(%s) %s %r>' %
                (self.__class__.__name__, self.name,
                 bbox2str(self.bbox), self.srcsize))


class LTAnon(LTItem, LTText):

    def __init__(self, text):
        self._text = text

    def get_text(self):
        return self._text


class LTChar(LTComponent, LTText):

    def __init__(self, matrix, font, fontsize, scaling, rise, text, textwidth, textdisp):
        LTText.__init__(self)
        self._text = text
        self.matrix = matrix
        self.fontname = font.fontname
        self.adv = textwidth * fontsize * scaling
        # compute the boundary rectangle.
        if font.is_vertical():
            # vertical
            width = font.get_width() * fontsize
            (vx,vy) = textdisp
            if vx is None:
                vx = width/2
            else:
                vx = vx * fontsize * .001
            vy = (1000 - vy) * fontsize * .001
            tx = -vx
            ty = vy + rise
            bll = (tx, ty+self.adv)
            bur = (tx+width, ty)
        else:
            # horizontal
            height = font.get_height() * fontsize
            descent = font.get_descent() * fontsize
            ty = descent + rise
            bll = (0, ty)
            bur = (self.adv, ty+height)
        (a,b,c,d,e,f) = self.matrix
        self.upright = (0 < a*d*scaling and b*c <= 0)
        (x0,y0) = apply_matrix_pt(self.matrix, bll)
        (x1,y1) = apply_matrix_pt(self.matrix, bur)
        if x1 < x0:
            (x0,x1) = (x1,x0)
        if y1 < y0:
            (y0,y1) = (y1,y0)
        LTComponent.__init__(self, (x0,y0,x1,y1))
        if font.is_vertical():
            self.size = self.width
        else:
            self.size = self.height

    def __repr__(self):
        return ('<%s %s matrix=%s font=%r adv=%s text=%r>' %
                (self.__class__.__name__, bbox2str(self.bbox), 
                 matrix2str(self.matrix), self.fontname, self.adv,
                 self.get_text()))

    def get_text(self):
        return self._text

    def is_compatible(self, obj):
        """Returns True if two characters can coexist in the same line."""
        return True

    
class LTContainer(LTComponent):

    def __init__(self, bbox):
        LTComponent.__init__(self, bbox)
        self._objs = []

    def __iter__(self):
        return iter(self._objs)

    def __len__(self):
        return len(self._objs)

    def add(self, obj):
        self._objs.append(obj)

    def extend(self, objs):
        for obj in objs:
            self.add(obj)

    def analyze(self, laparams):
        for obj in self._objs:
            obj.analyze(laparams)
    

class LTExpandableContainer(LTContainer):

    def __init__(self):
        LTContainer.__init__(self, (+INF,+INF,-INF,-INF))

    def add(self, obj):
        LTContainer.add(self, obj)
        self.set_bbox((min(self.x0, obj.x0), min(self.y0, obj.y0),
                       max(self.x1, obj.x1), max(self.y1, obj.y1)))


class LTTextContainer(LTExpandableContainer, LTText):

    def __init__(self):
        LTText.__init__(self)
        LTExpandableContainer.__init__(self)

    def get_text(self):
        return ''.join( obj.get_text() for obj in self if isinstance(obj, LTText) )
    

class LTTextLine(LTTextContainer):

    def __repr__(self):
        return ('<%s %s %r>' % (self.__class__.__name__, bbox2str(self.bbox), self.get_text()))
    
    def _insert_anon_spaces(self, word_margin):
        raise NotImplementedError()
    
    def add(self, obj):
        assert isinstance(obj, LTChar)
        LTTextContainer.add(self, obj)
    
    def analyze(self, laparams):
        LTTextContainer.analyze(self, laparams)
        word_margin = laparams.word_margin
        if laparams.heuristic_word_margin and any(obj.get_text() == ' ' for obj in self._objs):
            word_margin *= 5
        if word_margin:
            self._insert_anon_spaces(word_margin)
        LTContainer.add(self, LTAnon('\n'))
    
    def is_empty(self):
        # We consider a text line with no text (only whitespace) to be empty, and thus ignored
        # for textbox grouping so that we don't falsely consider a textbox a bunch of lines with
        # an empty line in the middle.
        if LTTextContainer.is_empty(self):
            return True
        return not self.get_text().strip()
    
    def find_neighbors(self, plane, ratio):
        raise NotImplementedError()

class LTTextLineHorizontal(LTTextLine):

    def __init__(self):
        LTTextLine.__init__(self)
        self._chars_by_height = None

    def _insert_anon_spaces(self, word_margin):
        insertpos = []
        for i, (prev, obj) in enumerate(trailiter(self._objs, skipfirst=True)):
            if prev.get_text() == ' ' or obj.get_text() == ' ':
                continue
            margin = word_margin * obj.width
            if prev.x1 < obj.x0-margin:
                insertpos.append(i+1) # +1 because our index is one behind because of trailiter
        # we invert insertpos so that inserting a char in the beginning doesn't affect the rest of
        # insertions.
        for pos in reversed(insertpos):
            self._objs.insert(pos, LTAnon(' '))
    
    def add(self, obj):
        LTTextLine.add(self, obj)
        self._chars_by_height = None
    
    def find_neighbors(self, plane, ratio):
        h = ratio*self.height
        objs = plane.find((self.x0, self.y0-h, self.x1, self.y1+h))
        # We use line_margin (ratio) as the threshold for line-height diff, which is somewhat
        # wrong, but in effect, the two number pretty much always go together. Well, future will
        # tell.
        max_height_diff = ratio
        acceptable = lambda obj: isinstance(obj, LTTextLineHorizontal) and\
            abs(obj.median_charheight - self.median_charheight) < max_height_diff
        return [obj for obj in objs if acceptable(obj)]
    
    @property
    def median_charheight(self):
        if not self._chars_by_height:
            chars = [o for o in self._objs if isinstance(o, LTChar)]
            self._chars_by_height = sorted(chars, key=lambda c: c.height)
        if self._chars_by_height:
            return self._chars_by_height[len(self._chars_by_height) // 2].height
        else:
            return 0
    

class LTTextLineVertical(LTTextLine):

    def _insert_anon_spaces(self, word_margin):
        insertpos = []
        for i, (prev, obj) in enumerate(trailiter(self._objs, skipfirst=True)):
            margin = word_margin * obj.height
            if obj.y1+margin < prev.y0:
                insertpos.append(i+1)
        for pos in reversed(insertpos):
            self._objs.insert(pos, LTAnon(' '))
    
    def find_neighbors(self, plane, ratio):
        w = ratio*self.width
        objs = plane.find((self.x0-w, self.y0, self.x1+w, self.y1))
        return [ obj for obj in objs if isinstance(obj, LTTextLineVertical) ]
    

##  A set of text objects that are grouped within
##  a certain rectangular area.

class LTTextBox(LTTextContainer):

    def __init__(self):
        LTTextContainer.__init__(self)
        self.index = None

    def __repr__(self):
        return ('<%s(%s) %s %r>' %
                (self.__class__.__name__,
                 self.index, bbox2str(self.bbox), self.get_text()))

class LTTextBoxHorizontal(LTTextBox):
    
    def __init__(self):
        LTTextBox.__init__(self)
        self._avg_lineheight = None
    
    def add(self, obj):
        LTTextBox.add(self, obj)
        self._avg_lineheight = None
    
    def analyze(self, laparams):
        LTTextBox.analyze(self, laparams)
        self._sort_lines()
    
    def _pos_in_box(self, obj):
        if self._avg_lineheight is None:
            self._avg_lineheight = sum(o.height for o in self._objs) / len(self._objs)
        x = obj.x0 - self.x0
        y = self.y1 - obj.y1
        # gridy is a y pos rounded using half the average line height. This way, we can be
        # confident that lines that have almost the same Y-pos will have the same gridy
        gridy = round(y / (self._avg_lineheight / 2))
        return x, y, gridy
    
    def _sort_lines(self):
        # Sorting lines in our textbox is not so easy. It's possible that we get some lines that
        # are obviously the same, but one of them is slightly higher or lower. In these cases,
        # simply sorting by Y-pos will be wrong. That's why we take the average line height to
        # "snap" our y-pos to some kind of grid. Then we sort by "snapped" ypos, using X pos as
        # a tie breaker.
        def sortkey(obj):
            x, y, gridy = self._pos_in_box(obj)
            return (gridy, x)
        
        self._objs = sorted(self._objs, key=sortkey)
    
    def get_writing_mode(self):
        return 'lr-tb'
    
    def paragraphs(self, indent_treshold):
        # Check if some lines in the box are indented and if yes, split our textbox in multiple
        # paragraphs and return the result.
        if len(self._objs) <= 5:
            # to avoid falsely separating non-paragraphs (like titles for example), we only consider
            # boxes of 6 lines or more.
            return [self]
        self._sort_lines()
        paragraphs = []
        current_paragraph = LTTextBoxHorizontal()
        prevgridy = None
        wasindented = False
        for obj in self._objs:
            x, y, gridy = self._pos_in_box(obj)
            if gridy != prevgridy:
                isinsdented = x > indent_treshold
                if isinsdented and (not wasindented) and (len(current_paragraph) > 1):
                    paragraphs.append(current_paragraph)
                    current_paragraph = LTTextBoxHorizontal()
                wasindented = isinsdented
                prevgridy = gridy
            current_paragraph.add(obj)
        if current_paragraph:
            paragraphs.append(current_paragraph)
        if len(paragraphs) > 1:
            return paragraphs
        else:
            return [self]
    

class LTTextBoxVertical(LTTextBox):

    def analyze(self, laparams):
        LTTextBox.analyze(self, laparams)
        self._objs = sorted(self._objs, key=lambda obj: -obj.x1)

    def get_writing_mode(self):
        return 'tb-rl'


class LTTextGroup(LTTextContainer):

    def __init__(self, objs):
        LTTextContainer.__init__(self)
        self.extend(objs)

class LTTextGroupLRTB(LTTextGroup):
    
    def analyze(self, laparams):
        LTTextGroup.analyze(self, laparams)
        # reorder the objects from top-left to bottom-right.
        self._objs = sorted(self._objs, key=lambda obj:
                           (1-laparams.boxes_flow)*(obj.x0) -
                           (1+laparams.boxes_flow)*(obj.y0+obj.y1))

class LTTextGroupTBRL(LTTextGroup):
    
    def analyze(self, laparams):
        LTTextGroup.analyze(self, laparams)
        # reorder the objects from top-right to bottom-left.
        self._objs = sorted(self._objs, key=lambda obj:
                           -(1+laparams.boxes_flow)*(obj.x0+obj.x1)
                           -(1-laparams.boxes_flow)*(obj.y1))


class LTLayoutContainer(LTContainer):

    def __init__(self, bbox):
        LTContainer.__init__(self, bbox)
        self.groups = None
        
    def get_textlines(self, laparams, objs):
        assert objs
        obj1 = objs[0]
        line = None
        for obj0, obj1 in trailiter(objs, skipfirst=True):
            k = 0
            if (obj0.is_compatible(obj1) and obj0.is_voverlap(obj1) and 
                min(obj0.height, obj1.height) * laparams.line_overlap < obj0.voverlap(obj1) and
                obj0.hdistance(obj1) < max(obj0.width, obj1.width) * laparams.char_margin):
                # obj0 and obj1 is horizontally aligned:
                #
                #   +------+ - - -
                #   | obj0 | - - +------+   -
                #   |      |     | obj1 |   | (line_overlap)
                #   +------+ - - |      |   -
                #          - - - +------+
                #
                #          |<--->|
                #        (char_margin)
                k |= 1
            if (laparams.detect_vertical and
                obj0.is_compatible(obj1) and obj0.is_hoverlap(obj1) and 
                min(obj0.width, obj1.width) * laparams.line_overlap < obj0.hoverlap(obj1) and
                obj0.vdistance(obj1) < max(obj0.height, obj1.height) * laparams.char_margin):
                # obj0 and obj1 is vertically aligned:
                #
                #   +------+
                #   | obj0 |
                #   |      |
                #   +------+ - - -
                #     |    |     | (char_margin)
                #     +------+ - -
                #     | obj1 |
                #     |      |
                #     +------+
                #
                #     |<-->|
                #   (line_overlap)
                k |= 2
            if ( (k & 1 and isinstance(line, LTTextLineHorizontal)) or
                 (k & 2 and isinstance(line, LTTextLineVertical)) ):
                line.add(obj1)
            elif line is not None:
                yield line
                line = None
            else:
                if k == 2:
                    line = LTTextLineVertical()
                    line.add(obj0)
                    line.add(obj1)
                elif k == 1:
                    line = LTTextLineHorizontal()
                    line.add(obj0)
                    line.add(obj1)
                else:
                    line = LTTextLineHorizontal()
                    line.add(obj0)
                    yield line
                    line = None
        if line is None:
            line = LTTextLineHorizontal()
            line.add(obj1)
        yield line

    def get_textboxes(self, laparams, lines):
        plane = Plane(lines)
        boxes = {}
        for line in lines:
            neighbors = line.find_neighbors(plane, laparams.line_margin)
            assert line in neighbors, line
            members = []
            for obj1 in neighbors:
                members.append(obj1)
                if obj1 in boxes:
                    members.extend(boxes.pop(obj1))
            if isinstance(line, LTTextLineHorizontal):
                box = LTTextBoxHorizontal()
            else:
                box = LTTextBoxVertical()
            for obj in uniq(members):
                box.add(obj)
                boxes[obj] = box
        done = set()
        for line in lines:
            box = boxes[line]
            if box in done: continue
            done.add(box)
            if laparams.paragraph_indent and isinstance(box, LTTextBoxHorizontal):
                paragraphs = box.paragraphs(laparams.paragraph_indent)
                for p in paragraphs:
                    yield p
            else:
                yield box

    def group_textboxes(self, laparams, boxes):
        def dist(obj1, obj2):
            """A distance function between two TextBoxes.
            
            Consider the bounding rectangle for obj1 and obj2.
            Return its area less the areas of obj1 and obj2, 
            shown as 'www' below. This value may be negative.
                    +------+..........+ (x1,y1)
                    | obj1 |wwwwwwwwww:
                    +------+www+------+
                    :wwwwwwwwww| obj2 |
            (x0,y0) +..........+------+
            """
            x0 = min(obj1.x0,obj2.x0)
            y0 = min(obj1.y0,obj2.y0)
            x1 = max(obj1.x1,obj2.x1)
            y1 = max(obj1.y1,obj2.y1)
            return ((x1-x0)*(y1-y0) - obj1.width*obj1.height - obj2.width*obj2.height)
        def isany(obj1, obj2):
            """Check if there's any other object between obj1 and obj2.
            """
            x0 = min(obj1.x0,obj2.x0)
            y0 = min(obj1.y0,obj2.y0)
            x1 = max(obj1.x1,obj2.x1)
            y1 = max(obj1.y1,obj2.y1)
            objs = set(plane.find((x0,y0,x1,y1)))
            return objs.difference((obj1,obj2))
        if len(boxes) > 100:
            # Grouping this many boxes would take too long and it doesn't make much sense to do so
            # considering the type of grouping (nesting 2-sized subgroups) that is done here.
            logger.warning("Too many boxes (%d) to group, skipping.", len(boxes))
            return boxes
        # XXX this still takes O(n^2)  :(
        dists = []
        for obj1, obj2 in combinations(boxes, 2):
            dists.append((0, dist(obj1, obj2), obj1, obj2))
        # we sort by dist and our tuple is (c,dist,obj1,obj2)
        sortkey = lambda tup: tup[:2]
        dists.sort(key=sortkey)
        plane = Plane(boxes)
        while dists:
            (c,d,obj1,obj2) = dists.pop(0)
            if c == 0 and isany(obj1, obj2):
                dists.append((1,d,obj1,obj2))
                continue
            if (isinstance(obj1, (LTTextBoxVertical, LTTextGroupTBRL)) or
                isinstance(obj2, (LTTextBoxVertical, LTTextGroupTBRL))):
                group = LTTextGroupTBRL([obj1,obj2])
            else:
                group = LTTextGroupLRTB([obj1,obj2])
            plane.remove(obj1)
            plane.remove(obj2)
            dists = [(c,d,o1,o2) for (c,d,o1,o2) in dists if o1 in plane and o2 in plane]
            for other in plane:
                dists.append((0, dist(group,other), group, other))
            dists.sort(key=sortkey)
            plane.add(group)
        assert len(plane) in {0, 1}
        return list(plane)
    
    def analyze(self, laparams):
        # textobjs is a list of LTChar objects, i.e.
        # it has all the individual characters in the page.
        (textobjs, otherobjs) = fsplit(lambda obj: isinstance(obj, LTChar), self._objs)
        for obj in otherobjs:
            obj.analyze(laparams)
        if not textobjs:
            return
        textlines = list(self.get_textlines(laparams, textobjs))
        assert len(textobjs) <= sum( len(line._objs) for line in textlines )
        (empties, textlines) = fsplit(lambda obj: obj.is_empty(), textlines)
        for obj in empties:
            obj.analyze(laparams)
        textboxes = list(self.get_textboxes(laparams, textlines))
        assert len(textlines) == sum( len(box._objs) for box in textboxes )
        groups = self.group_textboxes(laparams, textboxes)
        assigner = IndexAssigner()
        for group in groups:
            group.analyze(laparams)
            assigner.run(group)
        textboxes.sort(key=lambda box:box.index)
        self._objs = textboxes + otherobjs + empties
        self.groups = groups


class LTFigure(LTLayoutContainer):

    def __init__(self, name, bbox, matrix):
        self.name = name
        self.matrix = matrix
        (x,y,w,h) = bbox
        bbox = get_bound( apply_matrix_pt(matrix, (p,q))
                          for (p,q) in ((x,y), (x+w,y), (x,y+h), (x+w,y+h)) )
        LTLayoutContainer.__init__(self, bbox)

    def __repr__(self):
        return ('<%s(%s) %s matrix=%s>' %
                (self.__class__.__name__, self.name,
                 bbox2str(self.bbox), matrix2str(self.matrix)))

    def analyze(self, laparams):
        if not laparams.all_texts:
            return
        LTLayoutContainer.analyze(self, laparams)


class LTPage(LTLayoutContainer):

    def __init__(self, pageid, bbox, rotate=0):
        LTLayoutContainer.__init__(self, bbox)
        self.pageid = pageid
        self.rotate = rotate

    def __repr__(self):
        return ('<%s(%r) %s rotate=%r>' %
                (self.__class__.__name__, self.pageid,
                 bbox2str(self.bbox), self.rotate))

##  Plane
##
##  A set-like data structure for objects placed on a plane.
##  Can efficiently find objects in a certain rectangular area.
##  It maintains two parallel lists of objects, each of
##  which is sorted by its x or y coordinate.
##
class Plane:

    def __init__(self, objs=None, gridsize=50):
        self._objs = []
        self._grid = {}
        self.gridsize = gridsize
        if objs is not None:
            for obj in objs:
                self.add(obj)

    def __repr__(self):
        return ('<Plane objs=%r>' % list(self))

    def __iter__(self):
        return iter(self._objs)

    def __len__(self):
        return len(self._objs)

    def __contains__(self, obj):
        return obj in self._objs

    def _getrange(self, area):
        (x0,y0,x1,y1) = area
        for y in drange(y0, y1, self.gridsize):
            for x in drange(x0, x1, self.gridsize):
                yield (x,y)
    
    # add(obj): place an object.
    def add(self, obj):
        for k in self._getrange((obj.x0, obj.y0, obj.x1, obj.y1)):
            if k not in self._grid:
                r = []
                self._grid[k] = r
            else:
                r = self._grid[k]
            r.append(obj)
        self._objs.append(obj)

    # remove(obj): displace an object.
    def remove(self, obj):
        for k in self._getrange((obj.x0, obj.y0, obj.x1, obj.y1)):
            try:
                self._grid[k].remove(obj)
            except (KeyError, ValueError):
                pass
        self._objs.remove(obj)

    # find(): finds objects that are in a certain area.
    def find(self, area):
        (x0,y0,x1,y1) = area
        done = set()
        for k in self._getrange((x0,y0,x1,y1)):
            if k not in self._grid: continue
            for obj in self._grid[k]:
                if obj in done: continue
                done.add(obj)
                if (obj.x1 <= x0 or x1 <= obj.x0 or
                    obj.y1 <= y0 or y1 <= obj.y0): continue
                yield obj
