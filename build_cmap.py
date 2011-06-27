import sys
import os
import os.path as op
from subprocess import Popen

BASEPATH = op.dirname(__file__)

def runcmd(args):
    print(' '.join(args))
    p = Popen(' '.join(args), shell=True)
    p.wait()

def clean():
    folder = op.join(BASEPATH, 'pdfminer', 'cmap')
    files = os.listdir(folder)
    gz_files = [fn for fn in files if fn.endswith('.gz')]
    for fn in gz_files:
        path = op.join(folder, fn)
        print("Removing {}".format(path))
        os.remove(path)

def main():
    clean()
    CONVCMAP_PATH = op.join(BASEPATH, 'tools', 'conv_cmap.py')
    SRCFOLDER = op.join(BASEPATH, 'cmaprsrc')
    DSTFOLDER = op.join(BASEPATH, 'pdfminer', 'cmap')
    args = [sys.executable, CONVCMAP_PATH, DSTFOLDER, 'Adobe-CNS1', op.join(SRCFOLDER, 'cid2code_Adobe_CNS1.txt'), 'cp950', 'big5']
    runcmd(args)
    args = [sys.executable, CONVCMAP_PATH, DSTFOLDER, 'Adobe-GB1', op.join(SRCFOLDER, 'cid2code_Adobe_GB1.txt'), 'cp936', 'gb2312']
    runcmd(args)
    args = [sys.executable, CONVCMAP_PATH, DSTFOLDER, 'Adobe-Japan1', op.join(SRCFOLDER, 'cid2code_Adobe_Japan1.txt'), 'cp932', 'euc-jp']
    runcmd(args)
    args = [sys.executable, CONVCMAP_PATH, DSTFOLDER, 'Adobe-Korea1', op.join(SRCFOLDER, 'cid2code_Adobe_Korea1.txt'), 'cp949', 'euc-kr']
    runcmd(args)

if __name__ == '__main__':
    main()