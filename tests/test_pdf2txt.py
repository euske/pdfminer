import unittest
import tools.pdf2txt


class TestPdf2txtMethods(unittest.TestCase):

    def testUsage(self):
        expected = 100
        self.assertEqual(tools.pdf2txt.usage([]), expected)

    def testSetOptions(self):
        expected = "Hello\nWorld\nHello\nWorld\nH e l l o\nW o r l d\
        \nH e l l o\nW o r l d"
        document = open("../samples/simpl1.pdf")
        self.assertEqual(tools.pdf2txt.setOptions(document), expected)


if __name__ == '__main__':
    unittest.main()
