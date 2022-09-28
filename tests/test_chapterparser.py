import unittest
from pdfminer.chapterparser import ChapterParser
import tools.pdf2txt
import os


class TestChapterParser(unittest.TestCase):
    def test_cp_read_text(self):
        inpfp = 'samples/txts/test2.txt'
        expected = "Shjkdgakhsgdvjasbdmbasvjhdgasvjhbnas haVSHJABKHSV Jbjk"
        result = ChapterParser.cp_read_text(self, inpfp)
        self.assertEqual(result, expected)

    def test_splitManyChapters(self):

        text = """Chapter 1 textgoeshere
        Chapter 2 textgoeshereaigain
        chapter 3 finalchaptertext"""
        result = ChapterParser.cp_split(self, text)
        expected = [" textgoeshere\n        ",
                    " textgoeshereaigain\n        ",
                    " finalchaptertext"]
        self.assertEqual(result, expected)

    def test_splitOneChapter(self):
        text = "     Chapter 1       chaptercontent"
        result = ChapterParser.cp_split(self, text)
        expected = ["       chaptercontent"]

        self.assertEqual(result, expected)

    def test_splitNoChapter(self):
        text = "  helloworld      chaptercontent"
        result = ChapterParser.cp_split(self, text)
        expected = ["  helloworld      chaptercontent"]

        self.assertEqual(result, expected)

    def test_writeManyChapters(self):

        chapters = [" textgoeshere ",
                    " textgoeshereaigain ",
                    " finalchaptertext"]
        ChapterParser.cp_write_chapters(self, chapters, 'samples/txts/')

        inpfp1 = 'samples/txts/chapter1.txt'
        inpfp2 = 'samples/txts/chapter2.txt'
        inpfp3 = 'samples/txts/chapter3.txt'
        result1 = ChapterParser.cp_read_text(self, inpfp1)
        result2 = ChapterParser.cp_read_text(self, inpfp2)
        result3 = ChapterParser.cp_read_text(self, inpfp3)

        self.assertEqual(result1, chapters[0])
        self.assertEqual(result2, chapters[1])
        self.assertEqual(result3, chapters[2])

    def test_writeOneChapter(self):
        chapters = [" Singlechapter "]
        ChapterParser.cp_write_chapters(self, chapters, 'samples/txts/')
        inpfp1 = 'samples/txts/chapter1.txt'
        result1 = ChapterParser.cp_read_text(self, inpfp1)

        self.assertEqual(result1, chapters[0])

    def testSetOneOption(self):
        argv = ['pdf2txt.py', '-T', 'samples/simple1.pdf']

        (debug, caching, outtype, outfile, encoding, chapterSplit,
         imagewriter, stripcontrol, scale, layoutmode, pagenos,
         maxpages, password, rotation) = \
            tools.pdf2txt.setOptionsAndConvert(argv)
        self.assertEqual(chapterSplit, True)
        os.remove('chapter1.txt')

    def testSetManyOptions(self):
        argv = ['pdf2txt.py', '-T', '-t', 'text',
                '-m', '2', 'samples/simple1.pdf']

        (debug, caching, outtype, outfile, encoding, chapterSplit, imagewriter,
         stripcontrol, scale, layoutmode, pagenos,
         maxpages, password, rotation) = \
            tools.pdf2txt.setOptionsAndConvert(argv)
        self.assertEqual(chapterSplit, True)
        self.assertEqual(outtype, 'text')
        self.assertEqual(maxpages, 2)
        os.remove('chapter1.txt')

    def testSplitChapters(self):
        inpfp = 'samples/txts/test4.txt'
        outfp = 'samples/txts/'
        ChapterParser.split_chapters(self, inpfp, outfp)

        chapterfp1 = 'samples/txts/chapter1.txt'
        chapterfp2 = 'samples/txts/chapter2.txt'

        result1 = ChapterParser.cp_read_text(self, chapterfp1)
        result2 = ChapterParser.cp_read_text(self, chapterfp2)

        expected1 = " FirstTestChapter "
        expected2 = " SecondTestChapter"

        self.assertEqual(result1, expected1)
        self.assertEqual(result2, expected2)

    def testPdfToChapters(self):
        argv = ['pdf2txt.py', '-T', 'samples/testChapterSplit.pdf']
        tools.pdf2txt.setOptionsAndConvert(argv)

        chapterfp1 = 'chapter1.txt'
        chapterfp2 = 'chapter2.txt'

        result1 = ChapterParser.cp_read_text(self, chapterfp1)
        result2 = ChapterParser.cp_read_text(self, chapterfp2)

        expected1 = '\n\nText from ﬁrst chapter\u2029\n\n\x0c'
        expected2 = '\n\nSecond chapter\n\n\n\x0c'

        self.assertEqual(result1, expected1)
        self.assertEqual(result2, expected2)

        os.remove('chapter1.txt')
        os.remove('chapter2.txt')


if __name__ == '__main__':
    unittest.main()
