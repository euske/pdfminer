import unittest
import tools.pdf2txt


class TestPdf2txtMethods(unittest.TestCase):

    def testUsage(self):
        expected = 100
        self.assertEqual(tools.pdf2txt.usage(['']), expected)

    def testSetOptions(self):
        argv = ['pdf2txt.py', '-o', 'samples/test_outfp.txt', '-t', 'text',
                '-m', '2', 'samples/simple1.pdf']
        (debug, caching, outtype, outfile, encoding,
         imagewriter, stripcontrol, scale, layoutmode, pagenos,
         maxpages, password, rotation) = tools.pdf2txt.setOptions(argv)
        self.assertEqual(outtype, 'text')
        self.assertEqual(outfile, 'samples/test_outfp.txt')
        self.assertEqual(maxpages, 2)

    def testPdfToText(self):
        expected = "Hello \n\nWorld\n\nHello \n\nWorld\n\nH e l l o  \n\n" + \
                    "W o r l d\n\nH e l l o  \n\nW o r l d\n\n"
        argv = ['pdf2txt.py', '-o', 'samples/test_outfp.txt', '-t', 'text',
                'samples/simple1.pdf']
        tools.pdf2txt.setOptions(argv)
        outfp = open('samples/test_outfp.txt')
        result = outfp.read()
        result = result[:-1]
        outfp.close()
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
