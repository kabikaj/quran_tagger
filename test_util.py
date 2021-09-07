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

from util import normalise, rasm, check_ellipsis


class TestNormalise(unittest.TestCase):

    def test_norm_1(self):
        self.assertEqual(normalise('بسُرعةِِ'), 'بسرعه')

    def test_norm_2(self):
        self.assertEqual(normalise('فكّر'), 'فکر')

    def test_norm_3_nun(self):
        self.assertEqual(normalise('نُۨجِي'), 'ننجی')

    def test_norm_4_nun(self):
        self.assertEqual(normalise('ٱلۡعَٰلَمِینَ'), 'لعلمین')

    def test_norm_5_conj(self):
        self.assertEqual(normalise('والماء'), 'ولم')

    def test_norm_6_conj(self):
        self.assertEqual(normalise('فَالماء'), 'فلم')

    def test_norm_7_conj(self):
        self.assertEqual(normalise('فِي'), 'فی')

    def test_norm_8_conj(self):
        self.assertEqual(normalise('ولا'), 'ول')

    def test_norm_9_conj(self):
        self.assertEqual(normalise('َوَلا'), 'ول')

class TestRasm(unittest.TestCase):

    def test_rasm_1(self):
        self.assertEqual(rasm('بسرعه'), 'BSREH')

    def test_rasm_2_all(self):
        self.assertEqual(rasm('رزژدذڈوبکلتثپجحخځچسشصضطظعغڡفگمهقنیی'), 'RRRDDDWBKLBBBGGGGGSSCCTTEEFFKMHFBBY')

    def test_rasm_3_NQY(self):
        self.assertEqual(rasm('قوق'), 'FWQ')

    def test_rasm_4_NQY(self):
        self.assertEqual(rasm('ننجی'), 'BBGY')

    def test_rasm_5_NQY(self):
        self.assertEqual(rasm('لعلمین'), 'LELMBN')

    def test_rasm_6(self):
        self.assertEqual(rasm(normalise("إبراهيم")), "BRHBM")

    def test_rasm_7(self):
        self.assertEqual(rasm(normalise("ولا")), "WL")

    def test_rasm_8(self):
        self.assertEqual(rasm(normalise("وَلَا")), "WL")

#class TestEqual(unittest.TestCase):
#
#    def test_equal_1(self):
#        self.assertTrue(equal('بسُرعهٍ', 'بِسُرعَهٍ'))
#
#    def test_equal_2(self):
#        self.assertTrue(equal('بسرعه', 'بِسُرعَهٍ'))
#
#    def test_equal_3_alif_wasla(self):
#        self.assertTrue(equal(normalise("ا"), normalise("ٱ")))
#
#    def test_equal_4_alif_hamza(self):
#        self.assertTrue(equal(normalise("ا"), normalise("أ")))
#
#    def test_equal_5_alif_hamza_below(self):
#        self.assertTrue(equal(normalise("إ"), normalise("إ")))
#
#    def test_equal_6_alif_madda(self):
#        self.assertTrue(equal(normalise("ا"), normalise("آ")))
#
#    def test_equal_7_dagger_alif(self):
#        self.assertTrue(equal(normalise("ما"), normalise("مٰا")))
#
#    def test_equal_8_sukun(self):
#        self.assertTrue(equal(normalise("شيء"), normalise("شيْء")))


class TestCheck_ellipsis(unittest.TestCase):

    def test_check_ellipsis_01(self):
        s = "سسسس صصصص ظظظظظ السورة كلها"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "al_sura kullaha"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_02(self):
        s = "سسسس صصصص ظظظظظ الآية كلها"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "al_aya kullaha"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_03(self):
        s = "سسسس صصصص ظظظظظ الخ شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila end_noun_ha"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_04(self):
        s = "سسسس صصصص ظظظظظ حتى تمامها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun_ha"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_05(self):
        s = "سسسس صصصص ظظظظظ حتى خاتمتها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun_ha"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_06(self):
        s = "سسسس صصصص ظظظظظ حتى خاتمة الآية شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun al_aya"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_07(self):
        s = "سسسس صصصص ظظظظظ حتى خاتمة السورة كلها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun al_sura kullaha"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_08(self):
        s = "سسسس صصصص ظظظظظ حتى خاتمة سورة البقرة شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun surat sura_name1"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_09(self):
        s = "سسسس صصصص ظظظظظ حتى خاتمة الفاتحة شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun sura_name1"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_10(self):
        s = "سسسس صصصص ظظظظظ حتى خاتمة أم القرآن شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_noun sura_name1 sura_name2"
        r = check_ellipsis(words_rasm, 3)
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_11(self):
        print(11)
        s = "سسسس صصصص ظظظظظ حتى ختمها شششش"  # problem: khātimatun and khātamahā have the same rasm: GBMH; but no problem!
        s = "سسسس صصصص ظظظظظ حتى تختمها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_verb_ha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_12(self):
        print(12)
        s = "سسسس صصصص ظظظظظ إلى أن تختمها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb_ha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_13(self):
        print(13)
        s = "سسسس صصصص ظظظظظ إلى أن فرغ منها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb min_ha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_14(self):
        print(14)
        s = "سسسس صصصص ظظظظظ حتى فرغت منها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_verb min_ha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_15(self):
        print(15)
        s = "سسسس صصصص ظظظظظ حتى فرغت من الآية شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta end_verb min al_aya"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_16(self):
        print(16)
        s = "سسسس صصصص ظظظظظ إلى أن فرغت من الآية كلها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb min al_aya kullaha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_17(self):
        print(17)
        s = "سسسس صصصص ظظظظظ إلى أن تنقضي السورة كلها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb al_sura kullaha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_18(self):
        print(18)
        s = "سسسس صصصص ظظظظظ إلى أن تنقضي سورة البقرة شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb surat sura_name1"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_19(self):
        print(19)
        s = "سسسس صصصص ظظظظظ إلى أن تنقضي أم القرآن شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb sura_name1 sura_name2"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_20(self):
        print(20)
        s = "سسسس صصصص ظظظظظ إلى أن تنقضي آخرها شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb end_noun_ha"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)


    def test_check_ellipsis_21(self):
        print(21)
        s = "سسسس صصصص ظظظظظ إلى أن ختمت شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an end_verb"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_22(self):
        print(22)
        s = "سسسس صصصص ظظظظظ إلى أن قرأ شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an speech_verb"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_23(self):
        print(23)
        s = "سسسس صصصص ظظظظظ حتى قال شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta speech_verb"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_24(self):
        print(24)
        s = "سسسس صصصص ظظظظظ حتى انتهى الى شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "hatta to_verb ila"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_25(self):
        print(25)
        s = "سسسس صصصص ظظظظظ إلى أن أتى على الآية شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila an to_verb cala al_aya"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_26(self):
        print(26)
        s = "سسسس صصصص ظظظظظ إلى قوله شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila qawlihi"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_27(self):
        print(27)
        s = "سسسس صصصص ظظظظظ إلى قوله تعالى شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila qawlihi GOD"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_28(self):
        print(28)
        s = "سسسس صصصص ظظظظظ إلى قول تعالى شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila qawl GOD"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_29(self):
        print(29)
        s = "سسسس صصصص ظظظظظ إلى قوله عز وجل شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila qawlihi GOD wa_GOD"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_30(self):
        print(30)
        s = "سسسس صصصص ظظظظظ إلى قوله عز شأنه وجل ذكره شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila qawlihi GOD GOD_attribute wa_GOD GOD_attribute"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_31(self):
        print(31)
        s = "سسسس صصصص ظظظظظ إلى قول جعفر شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_32(self):
        print(32)
        s = "سسسس صصصص ظظظظظ إلى أن فعل شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "ila"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_33(self):
        print(33)
        s = "سسسس صصصص ظظظظظ الآية شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = False
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)

    def test_check_ellipsis_34(self):
        print(34)
        s = "سسسس صصصص ظظظظظ الآية إلى آخر الآيات شششش"
        words = s.split(" ")
        words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
        exp = "al_aya ila end_noun al_sura"
        r = check_ellipsis(words_rasm, 3)
        print(" ".join([x[2] for x in words_rasm]))
        print(r)
        self.assertEqual(r, exp)
        
if __name__ == '__main__':

    parser = ArgumentParser(description='apply all tests for util')
    args = parser.parse_args()

    unittest.main()
