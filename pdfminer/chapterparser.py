#!/usr/bin/env python
from operator import delitem
import os
import struct
import re



# encrypt(key, fin, fout, keybits=256)
class ChapterParser:
   
   def cp_read_text(self, inpfp):
        filehandle = open(inpfp)    
        text =  filehandle.read()
        filehandle.close()
        return text
    
   def cp_split(self, text):
        chapterList = re.split('Chapter ' +'\d+', text, flags=re.IGNORECASE)[1:]

        if chapterList == []:
            chapterList = [text]
        
        return chapterList
   def cp_write_chapters(self, chapters):
       for i, chapter in enumerate(chapters):
           outfp = 'samples/txts/chaper' + str(i+1) + '.txt' 
           
           with open(outfp, 'w') as f:
                f.write(chapter)    
       return