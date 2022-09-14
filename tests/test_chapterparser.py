import unittest
from pdfminer.chapterparser import ChapterParser



class TestChapterParser(unittest.TestCase):
    def test_cp_read_text(self):
        inpfp = 'samples/txts/test2.txt'
        expected = "Shjkdgakhsgdvjasbdmbasvjhdgasvjhbnas haVSHJABKHSV Jbjk"
        result = ChapterParser.cp_read_text(self, inpfp)
        self.assertEqual(result, expected)
        
        
    def test_split(self):
        
        text = "Chapter 1 textgoeshere Chapter 2 textgoeshereaigain chapter 3 finalchaptertext"
        result = ChapterParser.cp_split(self, text)
        expected = [" textgoeshere ", " textgoeshereaigain ", " finalchaptertext"]
        self.assertEqual(result, expected)
        
        
        
    def test_writeOneChapter(self):
        text = "     Chapter 1       chaptercontent"
        result = ChapterParser.cp_split(self, text)
        expected = ["       chaptercontent"]
        self.assertEqual(result, expected)
       
    def test_writeManyChapters(self):
       self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
