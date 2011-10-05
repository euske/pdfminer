import os.path as op

from pdfminer.layout import *
from .util import eq_, TestData, pages_from_pdf, extract_textboxes

testdata = TestData(op.join(op.dirname(__file__), '..', 'samples', 'layout'))

def test_small_elements_get_plane_grid_placement():
    # There was a bug where an element very small elements (int(x0) == int(x1) or int(y0) == int(y1))
    # would never be placed on any grid on a Plane.
    c = LTComponent((50.01, 42, 50.02, 44))
    p = Plane([c])
    assert p.find((0, 0, 50, 50))

def test_slightly_higher_text():
    # The 'slightly higher' part in this pdf is slightly higher. When we sort our elements in the
    # box, we want it to stay in its obvious place in the objects' order.
    path = testdata.filepath('slightly_higher.pdf')
    page = pages_from_pdf(path)[0]
    boxes = extract_textboxes(page)
    eq_(len(boxes), 1)
    assert boxes[0].get_text().startswith("This page has simple text with a\n*slightly* higher")

def test_paragraph_indents():
    # a textbox has a "paragraph" method that checks the indent of its lines and see if it's
    # possible to split the box in multiple paragraphs.
    path = testdata.filepath('paragraphs_indent.pdf')
    page = pages_from_pdf(path, paragraph_indent=5)[0]
    boxes = extract_textboxes(page)
    eq_(len(boxes), 3)
    assert boxes[0].get_text().startswith("First")
    assert boxes[1].get_text().startswith("Second")
    assert boxes[2].get_text().startswith("Third")

def test_centered_text():
    # In the case of a short piece of text with uneven line xpos, don't split each line into
    # "paragraphs".
    path = testdata.filepath('centered.pdf')
    page = pages_from_pdf(path, paragraph_indent=5)[0]
    boxes = extract_textboxes(page)
    eq_(len(boxes), 1)

def test_big_letter_with_title():
    # A line with a big first letter makes the whole line higher, which might make the layout
    # grouping algorithm think that a title line preceding it goes with that line.
    path = testdata.filepath('big_letter_and_title.pdf')
    page = pages_from_pdf(path)[0]
    boxes = extract_textboxes(page)
    eq_(len(boxes), 2)
    eq_(boxes[0].get_text(), "This is a title\n")
    assert boxes[1].get_text().startswith("And this is a paragraph")

def test_big_letter_spanning_multiple_lines():
    # When we have a paragraph starting with a big letter that spans multiple lines, count it as
    # a single paragraph. Previously, each line would be counted as a single paragraph.
    # In the test file, it's even trickier than usual because the big letter coords doesn't make
    # the big letter belong to the textbox (so we have an extra 'L' textbox, but we don't consider
    # it a bug). The file was created with Pages and this kind of layout is kinda hard to make with
    # it.
    path = testdata.filepath('big_letter_spanning_lines.pdf')
    page = pages_from_pdf(path, paragraph_indent=5)[0]
    boxes = extract_textboxes(page)
    eq_(len(boxes), 4) # 3 paragraph + the extra 'L'
    
def test_space_chars_only():
    # When a page would only contain space characters, we would have a crash because despite having
    # textobjs, we would have no textlines.
    path = testdata.filepath('space_chars_only.pdf')
    page = pages_from_pdf(path)[0]
    boxes = extract_textboxes(page) # no crash
    eq_(len(boxes), 0)