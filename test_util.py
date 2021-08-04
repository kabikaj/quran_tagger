#!/usr/bin/env python3
#
#    test_util.py
#
# usage:
#
#   apply all tests:
#     $ python test_util.py
#     $ python -m unittest test_util
#
#   apply specific test
#     $ python -m unittest test_util.TestNormalise
#
#################################################################################

import unittest
from argparse import ArgumentParser

from util import normalise, rasm, equal


class TestNormalise(unittest.TestCase):

    def test_norm_1(self):
        self.assertEqual(normalise('بسُرعةِِ'), 'بسُرعهٍ')

    def test_norm_2(self):
        self.assertEqual(normalise('فكّر'), 'کر')

    def test_norm_3_nun(self):
        self.assertEqual(normalise('نُۨجِي'), 'نُنجِی')

    def test_norm_4_nun(self):
        self.assertEqual(normalise('ٱلۡعَٰلَمِینَ'), 'لعَلَمِینَ')

    def test_norm_5_conj(self):
        self.assertEqual(normalise('والماء'), 'لم')

    def test_norm_6_conj(self):
        self.assertEqual(normalise('فَالماء'), 'لم')

    def test_norm_7_conj(self):
        self.assertEqual(normalise('فِي'), 'فِی')

class TestRasm(unittest.TestCase):

    def test_rasm_1(self):
        self.assertEqual(rasm('بسُرعهٍ'), 'BSREH')

    def test_rasm_2_NQY(self):
        self.assertEqual(rasm('قَوْق'), 'FWQ')

    def test_rasm_3_NQY(self):
        self.assertEqual(rasm('نُنجِی'), 'BBGY')

    def test_rasm_4_NQY(self):
        self.assertEqual(rasm('العَلَمِینَ'), 'LELMBN')

class TestEqual(unittest.TestCase):

    def test_equal_1(self):
        self.assertTrue(equal('بسُرعهٍ', 'بِسُرعَهٍ'))

    def test_equal_2(self):
        self.assertTrue(equal('بسرعه', 'بِسُرعَهٍ'))


if __name__ == '__main__':

    parser = ArgumentParser(description='apply all tests for util')
    args = parser.parse_args()

    unittest.main()
