#!/usr/bin/env python
import re


class ChapterParser:

    def cp_read_text(self, inpfp):
        filehandle = open(inpfp)
        text = filehandle.read()
        filehandle.close()
        return text

    def cp_split(self, text):
        chapterList = re.split(
            'Chapter ' + r'\d+', text, flags=re.IGNORECASE)[1:]

        if chapterList == []:
            chapterList = [text]

        return chapterList

    def cp_write_chapters(self, chapters, outpath):
        for i, chapter in enumerate(chapters):
            outfp = outpath + 'chapter' + str(i+1) + '.txt'

            with open(outfp, 'w') as f:
                f.write(chapter)
        return

    def split_chapters(self, inpfp, outpath):

        text = ChapterParser.cp_read_text(self, inpfp)
        chapterList = ChapterParser.cp_split(self, text)
        ChapterParser.cp_write_chapters(self, chapterList, outpath)

        return
