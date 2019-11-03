# PDFMiner

PDFMiner is a text extraction tool for PDF documents.

[![Build Status](https://travis-ci.org/euske/pdfminer.svg?branch=master)](https://travis-ci.org/euske/pdfminer)
[![PyPI](https://img.shields.io/pypi/v/pdfminer)](https://pypi.org/project/pdfminer/)

**Warning**: Starting from version 20191010, PDFMiner supports **Python 3 only**.
For Python 2 support, check out
<a href="https://github.com/pdfminer/pdfminer.six">pdfminer.six</a>.

## Features:

  * Pure Python (3.6 or above).
  * Supports PDF-1.7. (well, almost)
  * Obtains the exact location of text as well as other layout information (fonts, etc.).
  * Performs automatic layout analysis.
  * Can convert PDF into other formats (HTML/XML).
  * Can extract an outline (TOC).
  * Can extract tagged contents.
  * Supports basic encryption (RC4 and AES).
  * Supports various font types (Type1, TrueType, Type3, and CID).
  * Supports CJK languages and vertical writing scripts.
  * Has an extensible PDF parser that can be used for other purposes.


## How to Use:

  1. `> pip install pdfminer`
  1. `> pdf2txt.py samples/simple1.pdf`


## Command Line Syntax:

### pdf2txt.py

pdf2txt.py extracts all the texts that are rendered programmatically.
It also extracts the corresponding locations, font names, font sizes,
writing direction (horizontal or vertical) for each text segment.  It
does not recognize text in images. A password needs to be provided for
restricted PDF documents.

    > pdf2txt.py [-P password] [-o output] [-t text|html|xml|tag]
                 [-O output_dir] [-c encoding] [-s scale] [-R rotation]
                 [-Y normal|loose|exact] [-p pagenos] [-m maxpages]
                 [-S] [-C] [-n] [-A] [-V]
                 [-M char_margin] [-L line_margin] [-W word_margin]
                 [-F boxes_flow] [-d]
                 input.pdf ...

  * `-P password` : PDF password.
  * `-o output` : Output file name.
  * `-t text|html|xml|tag` : Output type. (default: automatically inferred from the output file name.)
  * `-O output_dir` : Output directory for extracted images.
  * `-c encoding` : Output encoding. (default: utf-8)
  * `-s scale` : Output scale.
  * `-R rotation` : Rotates the page in degree.
  * `-Y normal|loose|exact` : Specifies the layout mode. (only for HTML output.)
  * `-p pagenos` : Processes certain pages only.
  * `-m maxpages` : Limits the number of maximum pages to process.
  * `-S` : Strips control characters.
  * `-C` : Disables resource caching.
  * `-n` : Disables layout analysis.
  * `-A` : Applies layout analysis for all texts including figures.
  * `-V` : Automatically detects vertical writing.
  * `-M char_margin` : Speficies the char margin.
  * `-W word_margin` : Speficies the word margin.
  * `-L line_margin` : Speficies the line margin.
  * `-F boxes_flow` : Speficies the box flow ratio.
  * `-d` : Turns on Debug output.

### dumppdf.py

dumppdf.py is used for debugging PDFs.
It dumps all the internal contents in pseudo-XML format.

    > dumppdf.py [-P password] [-a] [-p pageid] [-i objid]
                 [-o output] [-r|-b|-t] [-T] [-O directory] [-d]
                 input.pdf ...

  * `-P password` : PDF password.
  * `-a` : Extracts all objects.
  * `-p pageid` : Extracts a Page object.
  * `-i objid` : Extracts a certain object.
  * `-o output` : Output file name.
  * `-r` : Raw mode. Dumps the raw compressed/encoded streams.
  * `-b` : Binary mode. Dumps the uncompressed/decoded streams.
  * `-t` : Text mode. Dumps the streams in text format.
  * `-T` : Tagged mode. Dumps the tagged contents.
  * `-O output_dir` : Output directory for extracted streams.

## TODO

  * Replace STRICT variable with something better.
  * Improve the debugging functions.
  * Use logging module instead of sys.stderr.
  * Proper test cases.
  * PEP-8 and PEP-257 conformance.
  * Better documentation.
  * Crypto stream filter support.


## Related Projects

  * <a href="http://pybrary.net/pyPdf/">pyPdf</a>
  * <a href="http://www.foolabs.com/xpdf/">xpdf</a>
  * <a href="http://pdfbox.apache.org/">pdfbox</a>
  * <a href="http://mupdf.com/">mupdf</a>
