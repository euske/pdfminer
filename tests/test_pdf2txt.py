import contextlib
import io
import shutil
import re
import unittest
import os
from unittest.mock import patch
from tools.pdf2txt import main


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
                main()
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

    def test_chapters_text_file(self):

        # Check if the files are created and then removes them in the end
        def tests(fake_stdout):
            path = 'samples/Crime_and_Punishment_T_short_chapters/'
            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.isfile(path + 'preface.txt'))

            # Cleaning up the files after creating them
            shutil.rmtree(path)

        self.run_tests(
            tests,
            [
                'pdf2txt.py',
                '-ch',
                'chapter',
                'samples/Crime_and_Punishment_T_short.pdf'
            ]
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
