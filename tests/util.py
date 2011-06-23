
def eq_(a, b, msg=None):
    __tracebackhide__ = True
    assert a == b, msg or "%r != %r" % (a, b)