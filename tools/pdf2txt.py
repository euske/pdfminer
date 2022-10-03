#!/usr/bin/env python
import argparse
import os
import sys

from pdfminer.cmapdb import CMapDB
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.image import ImageWriter
from pdfminer.layout import LAParams
from pdfminer.pdfdevice import TagExtractor
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


def main():
    """
    Converts pdf files into either txt, html or xml file.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='input.pdf', nargs='+')
    parser.add_argument('-P', '--password')
    parser.add_argument('-o', '--output')
    parser.add_argument('-t', '--text-type',
                        choices=['text', 'html', 'xml', 'tag'])
    parser.add_argument('-O', '--output-dir')
    parser.add_argument('-c', '--encoding')
    parser.add_argument('-s', '--scale')
    parser.add_argument('-R', '--rotation')
    parser.add_argument('-Y', '--layout-mode',
                        choices=['normal', 'loose', 'exact'])
    parser.add_argument('-p', '--pagenos')
    parser.add_argument('-m', '--maxpages')
    parser.add_argument('-S', '--strip-control', action='store_true')
    parser.add_argument('-C', '--disable-caching', action='store_true')
    parser.add_argument('-n', '--no-layout', action='store_true')
    parser.add_argument('-A', '--all-texts', action='store_true')
    parser.add_argument('-V', '--detect-vertical', action='store_true')
    parser.add_argument('-M', '--char-margin')
    parser.add_argument('-L', '--line-margin')
    parser.add_argument('-W', '--word-margin')
    parser.add_argument('-F', '--boxes-flow')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-ch', '--chapterize')
    args = parser.parse_args()

    # debug option
    debug = 0
    # input option
    password = b''
    pagenos = set()
    maxpages = 0
    # output option
    outfile = None
    outtype = None
    imagewriter = None
    rotation = 0
    stripcontrol = False
    layoutmode = 'normal'
    encoding = 'utf-8'
    scale = 1
    caching = True
    chapters = False
    chapter_definition = None

    laparams = LAParams()
    if args.debug:
        debug += 1
    if args.password:
        password = args.password.encode('ascii')
    if args.output:
        outfile = args.output
    if args.text_type:
        outtype = args.text_type
    if args.output_dir:
        imagewriter = ImageWriter(args['output-dir'])
    if args.encoding:
        encoding = args.encoding
    if args.scale:
        scale = float(args.scale)
    if args.rotation:
        rotation = int(args.rotation)
    if args.layout_mode:
        layoutmode = args.layout_mode
    if args.pagenos:
        pagenos.update(int(x) - 1 for x in args.pagenos.split(','))
    if args.maxpages:
        maxpages = int(args.maxpages)
    if args.strip_control:
        stripcontrol = True
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
    if args.chapterize:
        chapter_definition = args.chapterize
        chapters = True
        # If output flag is not used then we create one to
        # parse through and create chapter file
        if not args.output:
            outfile = 'chapters'

    #
    PDFDocument.debug = debug
    PDFParser.debug = debug
    CMapDB.debug = debug
    PDFPageInterpreter.debug = debug
    #
    rsrcmgr = PDFResourceManager(caching=caching)
    if not outtype:
        outtype = 'text'
        if outfile:
            if outfile.endswith('.htm') or outfile.endswith('.html'):
                outtype = 'html'
            elif outfile.endswith('.xml'):
                outtype = 'xml'
            elif outfile.endswith('.tag'):
                outtype = 'tag'
    if outfile:
        outfp = open(outfile, 'w', encoding=encoding)
    else:
        outfp = sys.stdout
    if outtype == 'text':
        device = TextConverter(rsrcmgr, outfp, laparams=laparams,
                               imagewriter=imagewriter)
    elif outtype == 'xml':
        device = XMLConverter(rsrcmgr, outfp, laparams=laparams,
                              imagewriter=imagewriter,
                              stripcontrol=stripcontrol)
    elif outtype == 'html':
        device = HTMLConverter(rsrcmgr, outfp, scale=scale,
                               layoutmode=layoutmode, laparams=laparams,
                               imagewriter=imagewriter, debug=debug)
    elif outtype == 'tag':
        device = TagExtractor(rsrcmgr, outfp)

    for fname in args.input:
        input_file_name = fname.split('/')[-1]
        # Get the input file name to create a directory with all the chapters
        input_file_name = input_file_name.replace('.pdf', '')
        with open(fname, 'rb') as fp:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(
                    fp, pagenos, maxpages=maxpages, password=password,
                    caching=caching, check_extractable=True
            ):
                page.rotate = (page.rotate + rotation) % 360
                interpreter.process_page(page)
    device.close()

    # Flag if we need to create separate file for each chapter or not
    # Creates folder for the chapters at the input file location.
    # It reads from the output file created by PDFPageInterpreter to
    # create separate txt for each chapter.
    if chapters:

        input_file_path = os.fspath(fname).replace('.pdf', '_chapters')
        os.makedirs(input_file_path, exist_ok=True)

        with open(outfile, 'r') as fp:

            chapters_name = 'preface' + '.txt'
            file = open(os.path.join(input_file_path, chapters_name), 'w')
            while True:
                cur_line = fp.readline()

                line = cur_line.split(' ')
                # To avoid making a new file when a chapter title
                # is mentioned in the text, we check that
                # the length of chapter is 3. ex.
                # If chapter title is "Chapter 3" == ['Chapter', '3', '\n']
                if len(line) == 3 and \
                        line[0].lower() == chapter_definition.lower():
                    file.close()
                    chapters_name = line[0] + line[1] + '.txt'
                    file = \
                        open(os.path.join(input_file_path, chapters_name), 'w')

                file.write(cur_line)
                if cur_line == '':
                    file.close()
                    print('Files were created successfully in ' +
                          str(os.path.join(input_file_path)))
                    break

    if outfile:
        outfp.close()
    # Deletes the file as it is only created to be parse through and create
    # different chapter file
    if not args.output and outfile is not None and os.path.isfile(outfile):
        os.remove(outfile)


if __name__ == '__main__':
    sys.exit(main())
