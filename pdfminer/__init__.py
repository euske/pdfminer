#!/usr/bin/env python
import os
__version__ = os.environ.get('PDFMINER_VERSION', '20140328')

if __name__ == '__main__':
    print (__version__)
