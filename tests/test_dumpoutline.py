import unittest
from tools.dumppdf import dumpoutline
import sys

class TestDumpOutline(unittest.TestCase):

  def test_dumpoutline(self):
    directory = 'samples/'
    files = ['ex1.pdf', 'ex2.pdf', 'example.pdf', 'jo.pdf', 'sample.pdf', 'simple1.pdf', 'simple2.pdf', 'simple3.pdf']
    objids = []
    pagenos = set()
    mode = None
    password = b''
    dumpall = False
    outfp = sys.stdout
    extractdir = None

    for file in files:
      result = dumpoutline(outfp, directory+file, objids, pagenos, password=password,
              dumpall=dumpall, mode=mode, extractdir=extractdir)

      notAllowed = '&<>"'

      self.assertFalse(set(notAllowed).intersection(result))


if __name__ == '__main__':
  unittest.main()