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
       delimiter = "Chapter"
       list = re.split('Chapter ' +'\d+', text, flags=re.IGNORECASE)[1:]
       
       
       return list
   def cp_write_chapters(self, chapters):
       return