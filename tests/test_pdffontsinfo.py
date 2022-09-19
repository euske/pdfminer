import contextlib
import io
import unittest
from unittest.mock import patch
from tools.pdffontsinfo import main


class TestPDFFonts(unittest.TestCase):

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
            ''' Testing if the output table has the following characteristics:

            Name                       Type     Encoding             Uni
            -------------------------- -------- -------------------- ---
            Times-Roman                Type 1   Custom               no
            Times-Bold                 Type 1   Standard             no
            Helvetica                  Type 1   Custom               no
            Helvetica-Bold             Type 1   Standard             no

            The table header: 4 titles: 'Name', 'Type', 'Encoding', 'Uni'.
            The width of the columns in chars is the following: 25 for Name,
                10 for Type, 20 for Encoding & 3 for Uni.
            Between each column there is a separating whitespace.
            The header is separated from the data with a sequence of dashes
                ('-') as the width of each column.

            This test is carried out with samples/simple1.pdf, the output
                should look like the following:

            Name                       Type     Encoding             Uni
            -------------------------- -------- -------------------- ---
            Helvetica                  Type 1   MacRomanEncoding     no

            Params:
                fake_stdout: a fake stdout mimicking the real output
                    of the program

            '''
            # Check the header titles
            self.assertIn(
                "Name".ljust(25)+" Type".ljust(10) +
                " Encoding".ljust(20)+" Uni".ljust(3),
                fake_stdout.getvalue())

            # Check the sequence of dashes
            self.assertIn(('-'*25)+" "+('-'*10)+" "+('-'*20) +
                          " "+('-'*3), fake_stdout.getvalue())

            # Check the values

            # Check Name
            self.assertIn("Helvetica", fake_stdout.getvalue())

            # Check Type
            self.assertIn("Type 1", fake_stdout.getvalue())

            # Check Encoding
            self.assertIn("MacRomanEncoding", fake_stdout.getvalue())

            # Check Uni
            self.assertIn("no", fake_stdout.getvalue())

        self.run_tests(tests, ['pdffonts.py', 'samples/simple1.pdf'])
