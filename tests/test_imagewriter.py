import unittest
from tools.pdf2txt import setOptionsAndConvert
import os
import shutil

_OUT_DIR = './samples/expected_output/'
_OUTPUT_ARG = '-O'
_TEST_OUTPUT_DIR = './samples/test_image_writer/'
_OUTPUT_FILE_FLAG = '-o'
_TMP_OUTPUT_FILE = 'tmp.txt'
_ARGV = ['',
         _OUTPUT_FILE_FLAG,
         _TMP_OUTPUT_FILE,
         _OUTPUT_ARG,
         _TEST_OUTPUT_DIR]


def equal_binary(f1, f2):
    with open(f1, 'rb') as f1_binary:
        with open(f2, 'rb') as f2_binary:
            return f1_binary.read() == f2_binary.read()


def check_output(expected_output, directory, count):
    """
    Checks whether the output images from pdf2txt is what is expected
    @param expected_output Array containing tuple with path to expected output
           content and expected output filename
    @param directory The output directory for pdf2txt
    @param count The number of expected output files
    """
    directory_content = os.listdir(directory)
    os.makedirs(directory, exist_ok=True)
    for i, expected_pair in enumerate(expected_output):
        if not equal_binary(expected_pair[0],
                            directory + '/' + expected_pair[1]):
            return False

    if len(directory_content) != count:
        print(f'{len(directory_content)} != {count}')
        return False
    return True


class TestImageWriter(unittest.TestCase):
    def test_jpg_colour(self):
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        setOptionsAndConvert(_ARGV + ['./samples/example-pdf-jpg.pdf'])
        self.assertTrue(
            check_output([(_OUT_DIR + 'example-pdf-jpg.jpg', 'X5.jpg')],
                         _TEST_OUTPUT_DIR,
                         1))

    def test_png_colour(self):
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        setOptionsAndConvert(_ARGV + ['./samples/example-pdf-png.pdf'])
        self.assertTrue(
            check_output([(_OUT_DIR + 'example-pdf-png.bmp',
                           'X5.800x600.bmp')],
                         _TEST_OUTPUT_DIR,
                         1))

    def test_png_grayscale(self):
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        setOptionsAndConvert(
            _ARGV + ['./samples/example-pdf-png-grayscale.pdf'])
        self.assertTrue(
            check_output([(_OUT_DIR + 'example-pdf-png-grayscale_2.bmp',
                           'X6.600x375.bmp'),
                          (_OUT_DIR + 'example-pdf-png-grayscale_1.bmp',
                           'X5.768x512.bmp')
                          ],
                         _TEST_OUTPUT_DIR,
                         2))
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        os.remove(_TMP_OUTPUT_FILE)


if __name__ == "__main__":
    unittest.main()
