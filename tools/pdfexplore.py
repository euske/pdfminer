import cmd, sys
from argparse import ArgumentParser

from pdfminer.pdftypes import PDFObjRef
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
        self.debug = False
        self.current_obj = None
        self.pdf_path = pdf_path
        self.fp = open(pdf_path, 'rb')
        self.parser = PDFParser(self.fp)
        self.doc = PDFDocument()
        self.parser.set_document(self.doc)
        self.doc.set_parser(self.parser)
        self.doc.initialize()
    
    def _cached_objects(self):
        return sorted(list(self.doc._cached_objs.items()) + list(self.doc._parsed_objs.items()))
    
    def _get_refs(self):
        result = []
        def search(obj, objid):
            if isinstance(obj, PDFObjRef):
                result.append((objid, obj))
            elif isinstance(obj, dict):
                for value in obj.values():
                    search(value, objid)
            elif isinstance(obj, list):
                for value in obj:
                    search(value, objid)
        objs = self._cached_objects()
        for objid, obj in objs:
            search(obj, objid)
        return result
    
    def precmd(self, line):
        if self.debug and line.strip() not in {'debug', 'quit', 'q'}:
            import pdb; pdb.set_trace()
        return line
    
    def do_debug(self, arg):
        "Toggles debug mode (perform actions in the debugger)."
        self.debug = not self.debug
        fmt = "Debug mode %s"
        mode = "ON" if self.debug else "OFF"
        print(fmt % mode)
    
    def do_status(self, arg):
        "Print current status, positions, etc.."
        print("Lexer pos: %d" % self.parser.lex.lexpos)
        print("File Length: %d" % self.parser.lex.lexlen)
        if self.current_obj:
            (objid, _, obj) = self.current_obj
        else:
            objid, obj = -1, "None"
        print("Current Object: %d %s" % (objid, obj))
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
    
    def do_robj(self, arg):
        "Read the next object and sets it as the 'current' object."
        objid, genno, obj = self.doc.readobj()
        self.current_obj = (objid, genno, obj)
        self.do_st('')
    
    @intarg()
    def do_sobj(self, arg):
        "Select object with ID X. The object has to have been read already."
        obj = None
        if arg in self.doc._cached_objs:
            obj = self.doc._cached_objs[arg]
        elif arg in self.doc._parsed_objs:
            obj = self.doc._parsed_objs[arg]
        else:
            print("Object hasn't been read yet.")
            strmid, index = self.doc.find_obj_ref(arg)
            if index is not None:
                print("However, our object id is in a xref")
                if strmid:
                    print("Stream ID: %d" % strmid)
                print("Position: %d" % index)
        if obj is not None:
            self.current_obj = (arg, 0, obj)
            self.do_st('')
    
    def do_dbgobj(self, arg):
        "Enter in debug mode with current obj as 'obj' in the local scope."
        if not self.current_obj:
            print("No current obj.")
            return
        objid, genno, obj = self.current_obj
        import pdb; pdb.set_trace()
    
    def do_readall(self, arg):
        "Read all objects in the document."
        self.doc._parse_everything()
        print("Read %d objects:" % len(self.doc._cached_objs))
        self.do_whatisread('')
    
    def do_dumpdata(self, arg):
        "For each read stream, print out the decoded data it contains."
        objs = self._cached_objects()
        for objid, obj in objs:
            print("Dumping obj id: %d" % objid)
            print(repr(obj))
            if hasattr(obj, 'get_data'):
                print(repr(obj.get_data()))
    
    def do_whatisread(self, arg):
        "Prints a list of all read object ids."
        objs = self._cached_objects()
        print(repr([objid for objid, obj in objs]))
    
    def do_refs(self, arg):
        "Look in all read objects and find all objects that reference to our current object."
        if not self.current_obj:
            print("No current obj.")
            return
        
        target_id, _, _ = self.current_obj
        result = [parent_id for parent_id, ref in self._get_refs() if ref.objid == target_id]
        print(repr(result))
    
    def do_deadrefs(self, arg):
        "Print (dead_id, host_id) for all dead references in the document."
        objs = self._cached_objects()
        objids = {objid for objid, obj in objs}
        result = [(ref.objid, parent_id) for parent_id, ref in self._get_refs() if ref.objid not in objids]
        print(repr(result))
    
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
