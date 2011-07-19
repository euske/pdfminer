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
