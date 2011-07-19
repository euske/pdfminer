import py.path

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.converter import PDFPageAggregator

def eq_(a, b, msg=None):
    __tracebackhide__ = True
    assert a == b, msg or "%r != %r" % (a, b)

class TestData:
    def __init__(self, datadirpath):
        self.datadirpath = py.path.local(datadirpath)
    
    def filepath(self, relative_path, *args):
        """Returns the path of a file in testdata.
        
        'relative_path' can be anything that can be added to a Path
        if args is not empty, it will be joined to relative_path
        """
        resultpath = self.datadirpath.join(relative_path)
        if args:
            resultpath = resultpath.join(*args)
        assert resultpath.check()
        return str(resultpath)

def pages_from_pdf(path, **laparams):
    fp = open(path, 'rb')
    doc = PDFDocument(caching=True)
    parser = PDFParser(fp)
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize()
    rsrcmgr = PDFResourceManager()
    laparams = LAParams(all_texts=True, **laparams)
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    result = []
    for page in doc.get_pages():
        interpreter.process_page(page)
        page_layout = device.get_result()
        result.append(page_layout)
    return result

def extract_from_elem(elem, lookfor):
    if isinstance(elem, lookfor):
        return [elem]
    else:
        try:
            return sum((extract_from_elem(subelem, lookfor) for subelem in elem), [])
        except TypeError:
            return []

def extract_textboxes(elem):
    return extract_from_elem(elem, lookfor=LTTextBox)