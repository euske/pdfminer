import sys
import argparse
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import PDFConverter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='input.pdf', nargs='+')
    parser.add_argument('-P', '--password')
    parser.add_argument('-o', '--output')
    parser.add_argument('-R', '--rotation')
    parser.add_argument('-p', '--pagenos')
    parser.add_argument('-m', '--maxpages')
    parser.add_argument('-C', '--disable-caching', action='store_true')
    parser.add_argument('-n', '--no-layout', action='store_true')
    parser.add_argument('-A', '--all-texts', action='store_true')
    parser.add_argument('-V', '--detect-vertical', action='store_true')
    parser.add_argument('-M', '--char-margin')
    parser.add_argument('-L', '--line-margin')
    parser.add_argument('-W', '--word-margin')
    parser.add_argument('-F', '--boxes-flow')
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()

    # debug option
    debug = 0
    # input option
    password = b''
    pagenos = set()
    maxpages = 0
    # output option
    outfile = None
    rotation = 0
    caching = True

    laparams = LAParams()
    if args.debug:
        debug += 1
    if args.password:
        password = args.password.encode('ascii')
    if args.output:
        outfile = args.output
    if args.rotation:
        rotation = int(args.rotation)
    if args.pagenos:
        pagenos.update(int(x)-1 for x in args.pagenos.split(','))
    if args.maxpages:
        maxpages = int(args.maxpages)
    if args.disable_caching:
        caching = False
    if args.no_layout:
        laparams = None
    if args.all_texts:
        laparams.all_texts = True
    if args.detect_vertical:
        laparams.detect_vertical = True
    if args.char_margin:
        laparams.char_margin = float(args.char_margin)
    if args.word_margin:
        laparams.word_margin = float(args.word_margin)
    if args.line_margin:
        laparams.line_margin = float(args.line_margin)
    if args.boxes_flow:
        laparams.boxes_flow = float(args.boxes_flow)

    #
    PDFDocument.debug = debug
    PDFParser.debug = debug
    CMapDB.debug = debug
    PDFPageInterpreter.debug = debug
    #

    rsrcmgr = PDFResourceManager(caching=caching)

    if outfile:
        outfp = open(outfile, 'w')
    else:
        outfp = sys.stdout

    device = PDFConverter(
        rsrcmgr, outfp, laparams=laparams)

    for fname in args.input:
        with open(fname, 'rb') as fp:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(
                fp,
                pagenos,
                maxpages=maxpages,
                password=password,
                caching=caching,
                check_extractable=True,
            ):
                page.rotate = (page.rotate + rotation) % 360
                interpreter.process_page(page)

        fonts = {
            'names': list(),
            'types': list(),
            'encoding': list(),
            'to_unicode': list()
        }

        # Collecting data from sources
        for fontkey in rsrcmgr._cached_fonts:
            # Font = class (PDFType1Font etc)
            font = rsrcmgr._cached_fonts[fontkey]
            # Type = TrueType/Type 1/Type 3/Type CID
            font_type = font.__class__.__name__
            # Name = Helvetica etc
            font_name = font.basefont

            font_enc = font.get_encoding_name()

            font_uni = font.get_toUnicode()

            fonts['names'].append(font_name)
            fonts['types'].append(font_type)
            fonts['encoding'].append(font_enc)
            fonts['to_unicode'].append(font_uni)

        device.close()
        outfp.write(fname+" fonts:\n")
        outfp.write(fonts2txt(fonts))
        outfp.write('\n')

        # delete the cache
        rsrcmgr._cached_fonts = {}
        fonts = {}

    if outfile:
        outfp.close()


def fonts2txt(fonts):
    ''' Transforms the font information in a nice text table following
        this pattern:

        Name                       Type     Encoding             Unicode
        -------------------------- -------- -------------------- -------
        Times-Roman                Type 1   Custom               no
        Times-Bold                 Type 1   Standard             no
        Helvetica                  Type 1   Custom               no
        Helvetica-Bold             Type 1   Standard             no

        The table header: 4 titles: 'Name', 'Type', 'Encoding', 'Unicode'.
        The width of the columns in chars is the following: 25 for Name,
            10 for Type, 20 for Encoding & 7 for Unicode.
        Between each column there is a separating whitespace.
        The header is separated from the data with a sequence of dashes
            ('-') as the width of each column.

        Params:
            - fonts : dictionary with 4 lists. The keys are the following:
                'names', 'types', 'encoding', 'to_unicode'
                All lists have the same number of items
                - names: list of strings with the names of the fonts
                - types: list of strings with the names of the types
                - enc: list of strings with the names of the encoding
                    types
                - uni: list of booleans that shows if it is unicode or not

    '''
    def process_line(name, type, encoding, unicode):
        '''
        Processes the table line to a nice distribution for the table disposal
        Params:
            -name: string with the name of the font
            -type: string with the type of the font (TrueType, Type 1,
                 Type 3 or Type CID)
            -encoding: string with the encoding of the font
            -unicode: string with the boolean representation of the'toUnicode'
                value of the font (yes or no)
        '''
        name_space = 25
        type_space = 10
        encoding_space = 20
        unicode_space = 7
        return name.ljust(name_space) + \
            ' ' + type.ljust(type_space) + \
            ' ' + encoding.ljust(encoding_space) + \
            ' ' + unicode.ljust(unicode_space)

    typename = {
        # Dictionary to change type name
        "PDFTrueTypeFont": "TrueType",
        "PDFType1Font": "Type 1",
        "PDFType3Font": "Type 3",
        "PDFCIDFont": "Type CID",
    }
    boolnames = {
        # Dictionary to change boolean names
        True: "Yes",
        False: "no",
    }

    table = process_line("Name", "Type", "Encoding", "Unicode") + "\n"
    table += process_line('-'*25, '-'*10, '-'*20, '-'*7) + "\n"

    if len(fonts['names']) == 0:
        table += process_line("(No font)",
                              "",
                              "",
                              "") + "\n"

    for i in range(len(fonts['names'])):
        # For all values process the lines
        table += process_line(fonts['names'][i],
                              typename[fonts['types'][i]],
                              fonts['encoding'][i],
                              boolnames[fonts['to_unicode'][i]]) + "\n"
    return table


if __name__ == '__main__':
    sys.exit(main())
