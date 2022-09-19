import unittest
import pdfminer.utils


class TestUtils(unittest.TestCase):

    def TestRightbbox2str(self):
        bbox = (25, 50, 30, 60)
        rightbbox = '30.000,60.000'
        self.assertEqual(rightbbox, pdfminer.utils.rightbbox2str(bbox))

    def TestLeftbbox2str(self):
        bbox = (25, 50, 30, 60)
        leftbbox = '25.000,50.000'
        self.assertEqual(leftbbox, pdfminer.utils.leftbbox2str(bbox))
