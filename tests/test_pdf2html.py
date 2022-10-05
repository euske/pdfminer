import unittest
import tools.pdf2txt


class TestHtml(unittest.TestCase):
    def test_html_conversion(self):
        argv = ['pdf2txt.py', '-o', 'samples/testHtml.html', '-t', 'html',
                'samples/ex1.pdf']
        tools.pdf2txt.setOptionsAndConvert(argv)
        with open('samples/testHtml.html', 'r') as a:
            with open('samples/sampleHtml.html', 'r') as b:
                output = a.read()
                expected = b.read()
                self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
