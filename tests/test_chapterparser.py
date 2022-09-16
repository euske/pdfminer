import unittest
from pdfminer.chapterparser import ChapterParser
import tools.pdf2txt 


class TestChapterParser(unittest.TestCase):
    def test_cp_read_text(self):
        inpfp = 'samples/txts/test2.txt'
        expected = "Shjkdgakhsgdvjasbdmbasvjhdgasvjhbnas haVSHJABKHSV Jbjk"
        result = ChapterParser.cp_read_text(self, inpfp)
        self.assertEqual(result, expected)
        
        
    def test_splitManyChapters(self):
        
        text = "Chapter 1 textgoeshere Chapter 2 textgoeshereaigain chapter 3 finalchaptertext"
        result = ChapterParser.cp_split(self, text)
        expected = [" textgoeshere ", " textgoeshereaigain ", " finalchaptertext"]
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
        
        chapters = [" textgoeshere ", " textgoeshereaigain ", " finalchaptertext"]

        ChapterParser.cp_write_chapters(self, chapters )
        
        inpfp1 = 'samples/txts/chaper1.txt'
        inpfp2 = 'samples/txts/chaper2.txt'
        inpfp3 = 'samples/txts/chaper3.txt'
        result1 = ChapterParser.cp_read_text(self, inpfp1)
        result2 = ChapterParser.cp_read_text(self, inpfp2)
        result3 = ChapterParser.cp_read_text(self, inpfp3)
        
        
        self.assertEqual(result1, chapters[0])
        self.assertEqual(result2, chapters[1])
        self.assertEqual(result3, chapters[2])
        
    def test_writeOneChapter(self):
        
        chapters = [" Singlechapter "]

        ChapterParser.cp_write_chapters(self, chapters )
        
        inpfp1 = 'samples/txts/chaper1.txt'
        
        result1 = ChapterParser.cp_read_text(self, inpfp1)

        self.assertEqual(result1, chapters[0])
        
    def testSetOneOption(self):
        argv = ['pdf2txt.py', '-T', '-o', 'samples/test_outfp.txt', 'samples/simple1.pdf']
        
        
        (debug, caching, outtype, outfile, encoding, chapterSplit,
         imagewriter, stripcontrol, scale, layoutmode, pagenos,
         maxpages, password, rotation) = \
        tools.pdf2txt.setOptionsAndConvert(argv)
        self.assertEqual(chapterSplit, True)
        
    def testSetManyOptions(self):
        argv = ['pdf2txt.py', '-T','-o', 'samples/test_outfp.txt', '-t', 'text',
                '-m', '2', 'samples/simple1.pdf']
        
        
        (debug, caching, outtype, outfile, encoding, chapterSplit,
         imagewriter, stripcontrol, scale, layoutmode, pagenos,
         maxpages, password, rotation) = \
        tools.pdf2txt.setOptionsAndConvert(argv)
        self.assertEqual(chapterSplit, True)
        self.assertEqual(outfile, 'samples/test_outfp.txt')
        self.assertEqual(maxpages, 2)
    


if __name__ == '__main__':
    unittest.main()
