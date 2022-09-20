#!/usr/bin/env python
import re




class ChapterParser:
    """
    This function reads a textfile from a filepath.

    @param inpfp: the filepath for the file to be read as a string.
    @return: The text in the given file as a string.
    
    """
    def cp_read_text(self, inpfp):
        filehandle = open(inpfp)
        text = filehandle.read()
        filehandle.close()
        return text


    """
    This function splits a string into substrings where it finds 
    some occurance of the text "Chapter" followed by a number

    @param text: The string to be split into multiple substrings.
    @return: A list containing multile substrings of chapters.
    
    """
    def cp_split(self, text):
        chapterList = re.split(
            'Chapter ' + r'\d+', text, flags=re.IGNORECASE)[1:]

        if chapterList == []:
            chapterList = [text]

        return chapterList

    """
    This function writes the content of each value of the chapters list into
    a unqiue file at the given output folder directory

    @param chapters: A list containing multile substrings of chapters.
    @param outpath: A string describing the directory of the generated txt files.
    
    
    """
    def cp_write_chapters(self, chapters, outpath):
        for i, chapter in enumerate(chapters):
            outfp = outpath + 'chapter' + str(i+1) + '.txt'

            with open(outfp, 'w') as f:
                f.write(chapter)
        return


    """
    This auxilliary function performs the full chapter split operation by 
    reading a textfile, splitting it and writing it anew.

    @param inpfp: A string describing the directory of the file containing the text to split.
    @param outpath: A string describing the directory of the generated txt files.
    
    
    """
    def split_chapters(self, inpfp, outpath):

        text = ChapterParser.cp_read_text(self, inpfp)
        chapterList = ChapterParser.cp_split(self, text)
        ChapterParser.cp_write_chapters(self, chapterList, outpath)

        return
