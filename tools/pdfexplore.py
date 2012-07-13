import cmd, sys
from argparse import ArgumentParser

from pdfminer.psparser import PSEOF
from pdfminer.pdfparser import PDFDocument, PDFParser

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def intarg(default=None):
    def decorator(func):
        def wrapper(self, arg):
            try:
                func(self, int(arg))
            except ValueError:
                if default is not None:
                    func(self, default)
                else:
                    print("Wrong position. Integer needed")
        return wrapper
    return decorator

class PDFExploreCmd(cmd.Cmd):
    prompt = '>>> '
    
    def __init__(self, pdf_path):
        cmd.Cmd.__init__(self)
        self.pdf_path = pdf_path
        self.fp = open(pdf_path, 'rb')
        self.parser = PDFParser(self.fp)
        self.doc = PDFDocument()
        self.parser.set_document(self.doc)
        self.doc.set_parser(self.parser)
        self.doc.initialize()
    
    def do_status(self, arg):
        "Print current status, positions, etc.."
        print("Lexer pos: %d" % self.parser.lex.lexpos)
        print("File Length: %d" % self.parser.lex.lexlen)
    do_st = do_status
    
    def do_xref(self, arg):
        "Print out the PDF's xrefs."
        for index, xref in enumerate(self.doc.xrefs, start=1):
            print("Xref #%d (%s)" % (index, xref.__class__.__name__))
            errors = []
            for objid in xref.get_objids():
                try:
                    _, pos = xref.get_pos(objid)
                    fmt = "%5d: %8d"
                    if pos >= self.parser.lex.lexlen:
                        fmt = "%5d: " + bcolors.WARNING + "%8d" + bcolors.ENDC
                    print(fmt % (objid, pos))
                except KeyError:
                    errors.append(objid)
            if errors:
                print("Errors on %s" % ', '.join(map(str, errors)))
    
    @intarg()
    def do_setpos(self, arg):
        "Set the current position of the parser to the offset supplied as an argument."
        self.parser.setpos(arg)
        self.parser.reset()
    
    @intarg(1)
    def do_rtok(self, arg):
        "Read the next X tokens, X being the supplied argument."
        tokens = []
        try:
            for _ in range(arg):
                pos, token = self.parser.nexttoken()
                token = str(token)
                if len(token) > 20:
                    token = token[:20] + "[...(%d)]" % (len(token)-20)
                tokens.append(token)
        except PSEOF:
            pass
        print(' '.join(tokens))
        if len(tokens) != arg:
            print("End of file reached")
    
    @intarg(1)
    def do_ptok(self, arg):
        "Peek the next X tokens, X being the supplied argument. Your current position will not change."
        pos = self.parser.lex.lexpos
        self.do_rtok(arg)
        self.do_setpos(pos)
    
    def do_quit(self, arg):
        "Quit PDFExplore"
        self.fp.close()
        sys.exit(0)
    do_q = do_quit
    

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('pdf_path', help="Path of the PDF file to explore")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    PDFExploreCmd(args.pdf_path).cmdloop()
