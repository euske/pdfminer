# Run pdf2txt on files in 'samples' (on the same level as this unit's parent folder) and compare
# them with their respective '.ref' file.

import sys
import os
import os.path as op
from subprocess import Popen

from .util import eq_

SAMPLES_PATH = op.join(op.dirname(__file__), '..', 'samples')
PDF2TXT_PATH = op.join(op.dirname(__file__), '..', 'tools', 'pdf2txt.py')

def runcmd(args):
    print(args)
    print(' '.join(args))
    p = Popen(' '.join(args), shell=True)
    p.wait()

def pytest_generate_tests(metafunc):
    if 'samplepath' in metafunc.funcargnames:
        paths_to_convert = []
        for root, dirs, files in os.walk(SAMPLES_PATH):
            for fn in files:
                if fn.endswith('.pdf'):
                    paths_to_convert.append(op.join(SAMPLES_PATH, root, fn))
        for path in paths_to_convert:
            samplepath = op.join(SAMPLES_PATH, path)
            metafunc.addcall(funcargs=dict(samplepath=samplepath))
    

def test_convert_sample(samplepath, tmpdir):
    EXTS = ['txt', 'html', 'xml']
    destfolder = str(tmpdir)
    assert op.exists(samplepath)
    dirname, filename = op.split(samplepath)
    without_ext = op.splitext(filename)[0]
    for ext in EXTS:
        ref = op.join(dirname, '{}.{}.ref'.format(without_ext, ext))
        dest = op.join(destfolder, '{}.{}'.format(without_ext, ext))
        assert op.exists(ref)
        args = [sys.executable, PDF2TXT_PATH, '-p1', '-V', '-o', dest, samplepath]
        runcmd(args)
        assert op.exists(dest)
        contents = open(dest, 'rt').read()
        ref_contents = open(ref, 'rt').read()
        eq_(contents, ref_contents)
