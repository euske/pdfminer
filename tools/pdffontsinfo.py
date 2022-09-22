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
    elif args.password:
        password = args.password.encode('ascii')
    elif args.output:
        outfile = args.output
    elif args.rotation:
        rotation = int(args.rotation)
    elif args.pagenos:
        pagenos.update(int(x)-1 for x in args.pagenos.split(','))
    elif args.maxpages:
        maxpages = int(args.maxpages)
    elif args.disable_caching:
        caching = False
    elif args.no_layout:
        laparams = None
    elif args.all_texts:
        laparams.all_texts = True
    elif args.detect_vertical:
        laparams.detect_vertical = True
    elif args.char_margin:
        laparams.char_margin = float(args.char_margin)
    elif args.word_margin:
        laparams.word_margin = float(args.word_margin)
    elif args.line_margin:
        laparams.line_margin = float(args.line_margin)
    elif args.boxes_flow:
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

        l_font_names = []
        l_font_types = []
        l_font_enc = []
        l_font_uni = []

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

            l_font_types.append(font_type)
            l_font_names.append(font_name)
            l_font_enc.append(font_enc)
            l_font_uni.append(font_uni)

        fonts = {}
        fonts['names'] = l_font_names
        fonts['types'] = l_font_types
        fonts['enc'] = l_font_enc
        fonts['uni'] = l_font_uni

        device.close()
        outfp.write(fname+" fonts:\n")
        outfp.write(fonts2txt(fonts))
        outfp.write('\n')

        # delete the cache
        rsrcmgr._cached_fonts = {}

    if outfile:
        outfp.close()


def fonts2txt(fonts):
    ''' Transforms the font information in a nice text table following
        this pattern:

        Name                       Type     Encoding             Uni
        -------------------------- -------- -------------------- ---
        Times-Roman                Type 1   Custom               no
        Times-Bold                 Type 1   Standard             no
        Helvetica                  Type 1   Custom               no
        Helvetica-Bold             Type 1   Standard             no

        The table header: 4 titles: 'Name', 'Type', 'Encoding', 'Uni'.
        The width of the columns in chars is the following: 25 for Name,
            10 for Type, 20 for Encoding & 3 for Uni.
        Between each column there is a separating whitespace.
        The header is separated from the data with a sequence of dashes
            ('-') as the width of each column.

        Params:
            - fonts : dictionary with 4 lists. The keys are the following:
                'names', 'types', 'enc', 'uni'
                All lists have the same number of items
                - names: list of strings with the names of the fonts
                - types: list of strings with the names of the types
                - enc: list of strings with the names of the encoding
                    types
                - uni: list of booleans that shows if it is unicode or not

    '''
    def process_line(list_info):
        '''
        Processes the table line to a nice distribution for the table disposal
        Params:
            -list_info: 4 string values are expected in the list, the name,
                the type, the encoding and the toUnicode value
        '''
        name_space = 25
        type_space = 10
        encoding_space = 20
        uni_space = 3
        return list_info[0].ljust(name_space) + \
            ' ' + list_info[1].ljust(type_space) + \
            ' ' + list_info[2].ljust(encoding_space) + \
            ' ' + list_info[3].ljust(uni_space)

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

    table = process_line(["Name", "Type", "Encoding", "Uni"]) + "\n"
    table += process_line(['-'*25, '-'*10, '-'*20, '-'*3]) + "\n"

    if len(fonts['names']) == 0:
        table += process_line(["(No font)",
                              "",
                               "",
                               ""]) + "\n"

    for i in range(len(fonts['names'])):
        # For all values process the lines
        table += process_line([fonts['names'][i],
                              typename[fonts['types'][i]],
                              fonts['enc'][i],
                              boolnames[fonts['uni'][i]]]) + "\n"
    return table


if __name__ == '__main__':
    sys.exit(main())
