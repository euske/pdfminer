import contextlib
import io
import re
import unittest
from unittest.mock import patch
from pdfminer.layout import LAParams
from tools.pdf2txt import create_chapters
from tools.pdf2txt import main, create_file


class TestPdf2Txt(unittest.TestCase):
    def run_tests(self, func_with_tests, args):
        """Runs the tests provided in func_with_tests with a fake stdout.

        Params:
            func_with_tests: a function that runs the actual tests. The
            function will receive the fake stdout as an argument.

            args: The arguments that will be passed to the main function
        """
        fake_stdout = io.StringIO()
        with contextlib.redirect_stdout(fake_stdout):
            with patch('sys.argv', args):
                main(args[1:])
                func_with_tests(fake_stdout)
        fake_stdout.close()

    def test_default(self):
        def tests(fake_stdout):
            self.assertIn("Hello", fake_stdout.getvalue())
            self.assertIn("W o r l d", fake_stdout.getvalue())

        self.run_tests(tests, ['pdf2txt.py', 'samples/simple1.pdf'])

    def test_html_output(self):
        def tests(fake_stdout):
            self.assertIn("Hello", fake_stdout.getvalue())
            self.assertIn("W o r l d", fake_stdout.getvalue())
            self.assertIn(
                "<html>",
                fake_stdout.getvalue(),
                'The output should have the html tag'
            )
            self.assertIn("<head>", fake_stdout.getvalue())

        self.run_tests(
            tests, ['pdf2txt.py', '-t', 'html', 'samples/simple1.pdf']
        )

    def test_equations_html_output(self):
        def tests(fake_stdout):
            # Assert that there are two lines between the equations
            self.assertRegex(
                fake_stdout.getvalue(),
                re.compile(
                    '<span.*border: black 1px solid.*'
                    '<span.*border: black 1px solid.*',
                    re.DOTALL
                )
            )

            # Assert that one of the equations are in the output
            self.assertRegex(fake_stdout.getvalue(), r'3.*x.*2.*\+ 5')

        self.run_tests(
            tests, ['pdf2txt.py', '-t', 'html', 'samples/equations.pdf']
        )

    def test_equations_xml_output(self):
        def tests(fake_stdout):
            # Assert that there are two lines between the equations
            self.assertRegex(
                fake_stdout.getvalue(),
                re.compile('<line.*<line', re.DOTALL)
            )
            # Assert that one of the equations are in the output
            self.assertRegex(
                fake_stdout.getvalue(),
                re.compile('3.*x.*2.*\\+.*5', re.DOTALL)
            )

        self.run_tests(
            tests, ['pdf2txt.py', '-t', 'xml', 'samples/equations.pdf']
        )

    def test_equations_text_output(self):
        def tests(fake_stdout):
            # Assert that the equation and the division line is in the output
            self.assertIn(
                "3x3\n\n"
                "-----\n"
                "3x2 + 5",
                fake_stdout.getvalue()
            )

        self.run_tests(
            tests, ['pdf2txt.py', 'samples/equations.pdf']
        )

    @patch('tools.pdf2txt.create_file')
    def test_create_html(self, mock_output):
        # Test for the '.html' files
        mock_output.return_value = True
        laparams = LAParams()
        debug = 0
        # input option
        password = b''
        pagenos = set()
        maxpages = 0
        # output option
        outfile = None  # If a file needs to be created
        outtype = 'html'
        imagewriter = None
        rotation = 0
        stripcontrol = False
        layoutmode = 'normal'
        encoding = 'utf-8'
        scale = 1
        caching = False
        input_file = ['samples/simple1.pdf']

        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertEqual(create_file_check, True)

        outfile = 'html'
        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertTrue(create_file_check)

        self.assertTrue(main(['-t', 'html', 'samples/simple1.pdf']))

    @patch('tools.pdf2txt.create_file')
    def test_create_xml(self, mock_output):
        # Test for the '.xml' files
        mock_output.return_value = True
        laparams = LAParams()
        debug = 0
        # input option
        password = b''
        pagenos = set()
        maxpages = 0
        # output option
        outfile = None  # If a file needs to be created
        outtype = 'xml'
        imagewriter = None
        rotation = 0
        stripcontrol = False
        layoutmode = 'normal'
        encoding = 'utf-8'
        scale = 1
        caching = False
        input_file = ['samples/simple1.pdf']

        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertEqual(create_file_check, True)

        outfile = 'xml'
        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertTrue(create_file_check)
        self.assertTrue(main(['-t', 'xml', 'samples/simple1.pdf']))

    @patch('tools.pdf2txt.create_file')
    def test_create_tag(self, mock_output):
        # Test for the '.tag' files
        mock_output.return_value = True
        laparams = LAParams()
        debug = 0
        # input option
        password = b''
        pagenos = set()
        maxpages = 0
        # output option
        outfile = None  # If a file needs to be created
        outtype = 'tag'
        imagewriter = None
        rotation = 0
        stripcontrol = False
        layoutmode = 'normal'
        encoding = 'utf-8'
        scale = 1
        caching = False
        input_file = ['samples/simple1.pdf']

        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertEqual(create_file_check, True)

        outfile = 'tag'
        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertTrue(create_file_check)

        self.assertTrue(main(['-t', 'tag', 'samples/simple1.pdf']))

    @patch('tools.pdf2txt.create_file')
    def test_create_text(self, mock_output):
        # Test for the '.text' files
        mock_output.return_value = True
        laparams = LAParams()
        debug = 0
        # input option
        password = b''
        pagenos = set()
        maxpages = 0
        # output option
        outfile = None  # If a file needs to be created
        outtype = 'text'
        imagewriter = None
        rotation = 0
        stripcontrol = False
        layoutmode = 'normal'
        encoding = 'utf-8'
        scale = 1
        caching = False
        input_file = ['samples/simple1.pdf']

        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertEqual(create_file_check, True)

        outfile = 'text'
        create_file_check = create_file(debug, caching, outfile, laparams,
                                        imagewriter,
                                        stripcontrol, scale, layoutmode,
                                        pagenos,
                                        maxpages, password, rotation, encoding,
                                        input_file, outtype)
        self.assertTrue(create_file_check)

        self.assertTrue(
            main(['-t', 'text', 'samples/Crime_and_Punishment_T_short.pdf']))

    @patch('tools.pdf2txt.create_chapters')
    def test_create_create_chapters(self, mock_output):
        # Test for the '.html' files
        mock_output.return_value = True
        laparams = LAParams()
        debug = 0
        # input option
        password = b''
        pagenos = set()
        maxpages = 0
        # output option
        outfile = 'chapters'  # If a file needs to be created
        outtype = ''
        imagewriter = None
        rotation = 0
        stripcontrol = False
        layoutmode = 'normal'
        encoding = 'utf-8'
        scale = 1
        caching = False
        chapter_definition = 'chapter'
        input_file = ['samples/Crime_and_Punishment_T_short.pdf']

        create_file_check = create_chapters(debug, caching, outfile, laparams,
                                            imagewriter,
                                            stripcontrol, scale, layoutmode,
                                            pagenos,
                                            maxpages, password, rotation,
                                            encoding, input_file, outtype,
                                            chapter_definition)
        self.assertEqual(create_file_check, True)

        self.assertTrue(main(
            ['-ch', 'chapters', 'samples/Crime_and_Punishment_T_short.pdf']))


if __name__ == '__main__':
    unittest.main()
