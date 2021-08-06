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

    def test_rasm_2_all(self):
        self.assertEqual(rasm('رزژدذڈوبکلتثپجحخځچسشصضطظعغڡفگمهقنیی'), 'RRRDDDWBKLBBBGGGGGSSCCTTEEFFKMHFBBY')

    def test_rasm_3_NQY(self):
        self.assertEqual(rasm('قَوْق'), 'FWQ')

    def test_rasm_4_NQY(self):
        self.assertEqual(rasm('نُنجِی'), 'BBGY')

    def test_rasm_5_NQY(self):
        self.assertEqual(rasm('العَلَمِینَ'), 'LELMBN')

class TestEqual(unittest.TestCase):

    def test_equal_1(self):
        self.assertTrue(equal('بسُرعهٍ', 'بِسُرعَهٍ'))

    def test_equal_2(self):
        self.assertTrue(equal('بسرعه', 'بِسُرعَهٍ'))

    def test_equal_3_alif_wasla(self):
        self.assertTrue(equal("ا", "ٱ"))

    def test_equal_4_alif_hamza(self):
        self.assertTrue(equal("ا", "أ"))

    def test_equal_5_alif_hamza_below(self):
        self.assertTrue(equal("ا", "إ"))

    def test_equal_6_alif_madda(self):
        self.assertTrue(equal("ا", "آ"))

    def test_equal_7_dagger_alif(self):
        self.assertTrue(equal("ما", "مٰا"))

    def test_equal_8_sukun(self):
        self.assertTrue(equal("شيء", "شيْء"))




if __name__ == '__main__':

    parser = ArgumentParser(description='apply all tests for util')
    args = parser.parse_args()

    unittest.main()
