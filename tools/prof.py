#!/usr/bin/env python
import sys


def prof_main(argv):
    import cProfile
    import pstats

    def usage():
        print('usage: %s module.function [args ...]' % argv[0])
        return 100
    args = argv[1:]
    if len(args) < 1:
        return usage()
    name = args.pop(0)
    prof = name+'.prof'
    lefti = name.index('.')
    i = name.rindex('.')
    (modname, funcname) = (name[:i], name[i+1:])
    module = __import__(modname, fromlist=[name[:lefti]])
    func = getattr(module, funcname)
    if args:
        args.insert(0, argv[0])
        cProfile.runctx('func(args)', globals(), locals(), prof)
        stats = pstats.Stats(prof)
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(1000)
    return


if __name__ == '__main__':
    sys.exit(prof_main(sys.argv))
