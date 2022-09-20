import unittest
import tools.pdf2txt


class TestWordprinting(unittest.TestCase):

    def testWordReader(self):

        argv = ['pdf2txt.py', '-o', 'samples/testxml.xml', '-t', 'xml',
                'samples/XMLConverterTestFile.pdf']
        tools.pdf2txt.setOptionsAndConvert(argv)
        with open('samples/testxml.xml', 'r') as f:
            charCoordinateArray = []
            for line in f:
                if 'word' in line:
                    try:
                        sub1 = line.split('bbox=')[1:]
                        wordCoordinates = sub1[0].split('>')[0]
                        firstString = charCoordinateArray[0]
                        secondString = charCoordinateArray[
                            len(charCoordinateArray)-2]
                        firstCharCoordinates = firstString.split(',')
                        secondCharCoordinates = secondString.split(',')
                        n = 2
                        left = ','.join(firstCharCoordinates[:n])
                        right = ','.join(secondCharCoordinates[n:])
                        self.assertEqual(wordCoordinates, left+","+right)
                        charCoordinateArray.clear()
                    except IndexError:
                        print("index error")
                else:
                    if '<text ' and '</text>' in line:
                        if 'bbox=' in line:
                            try:
                                sub1 = line.split('bbox=')[1]
                                charCoordinateArray.append(sub1.split(' ')[0])
                            except IndexError:
                                print("index error 2")


class TestLineCoordinates(unittest.TestCase):

    def testLineReader(self):

        argv = ['pdf2txt.py', '-o', 'samples/testxml.xml', '-t', 'xml',
                'samples/simple1.pdf']
        tools.pdf2txt.setOptionsAndConvert(argv)
        with open('samples/testxml.xml', 'r') as f:
            charCoordinateArray = []
            lineCoordinate = ''
            for line in f:
                if '<textline>' in line:
                    sub1 = line.split('bbox=')[1]
                    lineCoordinate = sub1.split(' ')[0]
                elif '<text ' and '</text>' in line:
                    sub1 = line.split('bbox=')[1]
                    charCoordinateArray.append(sub1.split(' ')[0])
                elif '</textline>' in line:
                    firstString = charCoordinateArray[1]
                    secondString = charCoordinateArray[
                        len(charCoordinateArray)-1]
                    firstCharCoordinates = firstString.split(',')
                    secondCharCoordinates = secondString.split(',')
                    n = 2
                    left = ','.join(firstCharCoordinates[:n])
                    right = ','.join(secondCharCoordinates[n:])
                    self.assertEqual(lineCoordinate, left+","+right)
                    charCoordinateArray.clear


if __name__ == '__main__':
    unittest.main()
