#!/usr/bin/env python
import sys
from pdfminer.cmapdb import convert_cmap

# main
def main(argv):
    import getopt

    def usage():
        print('usage: %s [-c enc=codec] output_dir regname [cid2code.txt ...]' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'c:')
    except getopt.GetoptError:
        return usage()
    enc2codec = {}
    for (k, v) in opts:
        if k == '-c':
            (enc,_,codec) = v.partition('=')
            enc2codec[enc] = codec
    if not args: return usage()
    outdir = args.pop(0)
    if not args: return usage()
    regname = args.pop(0)

    convert_cmap(outdir, regname, enc2codec, args)
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
