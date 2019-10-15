#!/usr/bin/env python
from setuptools import setup
from setuptools.command.install import install
from pdfminer import __version__

class install_cmap(install):

    def run(self):
        import os.path
        import pdfminer
        from pdfminer.cmapdb import convert_cmap
        outdir = os.path.join(os.path.join(self.install_lib, 'pdfminer'), 'cmap')
        print('installing cmap: %r...' % outdir)
        os.makedirs(outdir, exist_ok=True)
        convert_cmap(
            outdir, 'Adobe-CNS1',
            {'B5':'cp950', 'UniCNS-UTF8':'utf-8'},
            ['cmaprsrc/cid2code_Adobe_CNS1.txt'])
        convert_cmap(
            outdir, 'Adobe-GB1',
            {'GBK-EUC':'cp936', 'UniGB-UTF8':'utf-8'},
            ['cmaprsrc/cid2code_Adobe_GB1.txt'])
        convert_cmap(
            outdir, 'Adobe-Japan1',
            {'RKSJ':'cp932', 'EUC':'euc-jp', 'UniJIS-UTF8':'utf-8'},
            ['cmaprsrc/cid2code_Adobe_Japan1.txt'])
        convert_cmap(
            outdir, 'Adobe-Korea1',
            {'KSC-EUC':'euc-kr', 'KSC-Johab':'johab', 'KSCms-UHC':'cp949',
             'UniKS-UTF8':'utf-8'},
            ['cmaprsrc/cid2code_Adobe_Korea1.txt'])
        install.run(self)
        return

setup(
    cmdclass = { 'install': install_cmap },
    name = 'pdfminer',
    version = __version__,
    description = 'PDF parser and analyzer',
    long_description = '''PDFMiner is a tool for extracting information from PDF documents.
Unlike other PDF-related tools, it focuses entirely on getting
and analyzing text data. PDFMiner allows to obtain
the exact location of texts in a page, as well as
other information such as fonts or lines.
It includes a PDF converter that can transform PDF files
into other text formats (such as HTML). It has an extensible
PDF parser that can be used for other purposes instead of text analysis.''',
    license = 'MIT',
    author = 'Yusuke Shinyama',
    author_email = 'yusuke@shinyama.jp',
    url = 'http://github.com/euske/pdfminer',
    packages = [
        'pdfminer',
    ],
    install_requires = [
        'pycryptdome',
    ],
    scripts=[
        'tools/pdf2txt.py',
        'tools/dumppdf.py',
    ],
    keywords=[
        'pdf parser',
        'pdf converter',
        'layout analysis',
        'text mining'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing',
    ],
)
