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


def check_output(expected_output, directory, count):
    """
    Checks whether the output images from pdf2txt is what is expected
    @param expected_output The path expected output files in an array
    @param directory The output directory for pdf2txt
    @param count The number of expected output files
    """
    directory_content = os.listdir(directory)
    os.makedirs(directory, exist_ok=True)
    for i, f in enumerate(directory_content):
        with open(expected_output[i], 'rb') as expected:
            with open(directory + '/' + f, 'rb') as output:
                if expected.read() != output.read():
                    print(f'{expected_output[i]} != {f}')
                    return False
    return len(directory_content) == count


class TestImageWriter(unittest.TestCase):
    def test_jpg_colour(self):
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        setOptionsAndConvert(_ARGV + ['./samples/example-pdf-jpg.pdf'])
        self.assertTrue(
            check_output([_OUT_DIR + 'example-pdf-jpg.jpg'],
                         _TEST_OUTPUT_DIR,
                         1))

    def test_png_colour(self):
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        setOptionsAndConvert(_ARGV + ['./samples/example-pdf-png.pdf'])
        self.assertTrue(
            check_output([_OUT_DIR + 'example-pdf-png.bmp'],
                         _TEST_OUTPUT_DIR,
                         1))

    def test_png_grayscale(self):
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        setOptionsAndConvert(
            _ARGV + ['./samples/example-pdf-png-grayscale.pdf'])
        self.assertTrue(
            check_output([_OUT_DIR + 'example-pdf-png-grayscale_2.bmp',
                          _OUT_DIR + 'example-pdf-png-grayscale_1.bmp'],
                         _TEST_OUTPUT_DIR,
                         2))
        shutil.rmtree(_TEST_OUTPUT_DIR, ignore_errors=True)
        os.remove(_TMP_OUTPUT_FILE)


if __name__ == "__main__":
    unittest.main()
