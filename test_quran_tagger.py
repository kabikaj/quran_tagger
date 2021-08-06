#!/usr/bin/env python3
#
#    test_quran_tagger.py
#
# usage:
#
#   apply all tests:
#     $ python test_quran_tagger.py
#     $ python -m unittest test_quran_tagger
#
#   apply specific test
#     $ python -m unittest test_quran_tagger.TestEqual
#
#################################################################################

import unittest
from argparse import ArgumentParser

from quran_tagger import equal, tagger


class TestTagger(unittest.TestCase):

    pass

    #TODO
    #def test_equal_1(self):
    #    self.assertTrue(equal('بسُرعهٍ', 'بِسُرعَهٍ'))


if __name__ == '__main__':

    parser = ArgumentParser(description='apply all tests for tagger')
    args = parser.parse_args()

    unittest.main()
