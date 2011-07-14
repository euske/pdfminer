
from pdfminer.layout import *

def test_small_elements_get_plane_grid_placement():
    # There was a bug where an element very small elements (int(x0) == int(x1) or int(y0) == int(y1))
    # would never be placed on any grid on a Plane.
    c = LTComponent((50.01, 42, 50.02, 44))
    p = Plane([c])
    assert p.find((0, 0, 50, 50))