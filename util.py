#!/usr/bin/env python3
#
#    util.py
#
# utility functions for quran_tagger.py
#
# requirements:
#   * quran-uthmani.json
#
# examples:
#   $ cat data/quran-simple.txt | python util.py --prepare_quran > quran_simple.json
#   $ cat data/quran-uthmani.txt | python util.py --prepare_quran > quran_uthmani.json
#   $ cat qc_quran.json | python util.py --prepare_stopwords > stopwords2.json
#
# echo وسلم فأما من أعطى واتقى وصدق بالحسنى إلى قوله فسنيسره للعسرى | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 3 --debug
#           فأما ... word_ini=1 word_end=9  qini=[92, 5, 1](77047) qend=[92, 7, 1](77053)
#
#################################################################################

import re
import sys
import textwrap
from itertools import groupby
from argparse import ArgumentParser, FileType

try:
    import ujson as json
except ModuleNotFoundError:
    import json

NORM_MAPPING = {
    #'ࣱ' : 'ٌ',
    #'ُُ' : 'ٌ',
    #'ࣰ' : 'ً',
    #'ََ' : 'ً',
    #'ࣲ' : 'ٍ',
    #'ِِ' : 'ٍ',
    'ة' : 'ه',
    'ہ' : 'ه',
    'ھ' : 'ه',
    'ﻫ' : 'ه',
    'إ' : 'ا',
    'أ' : 'ا',
    'آ' : 'ا',
    'ٱ' : 'ا',
    'ؤ' : 'و',
    'ٮ' : 'ی',
    'ى' : 'ی',
    'ي' : 'ی',
    'ئ' : 'ی',
    'ﺑ' : 'ب',
    'ﮐ' : 'ک',
    'ك' : 'ک',
    'ﻟ' : 'ل',
    'ں' : 'ن',
    'ۨ' : 'ن',
}

RASM_MAPPING = {
    #'ا'  : 'A',
    'ر'  : 'R',
    'ز'  : 'R',
    'ژ'  : 'R',
    'د'  : 'D',
    'ذ'  : 'D',
    'ڈ'  : 'D',
    'و'  : 'W',
    'ب'  : 'B',
    'ک'  : 'K',
    'ل'  : 'L',
    'ت'  : 'B',
    'ث'  : 'B',
    'پ'  : 'B',
    'ج'  : 'G',
    'ح'  : 'G',
    'خ'  : 'G',
    'ځ'  : 'G',
    'چ'  : 'G',
    'س'  : 'S',
    'ش'  : 'S',
    'ص'  : 'C',
    'ض'  : 'C',
    'ط'  : 'T',
    'ظ'  : 'T',
    'ع'  : 'E',
    'غ'  : 'E',
    'ڡ'  : 'F',
    'ف'  : 'F',
    'گ'  : 'K',
    'م'  : 'M',
    'ه'  : 'H',
    'ق'  : 'F',
    'ن'  : 'B',
    'ی'  : 'B',
}

QNY_RASM_MAPPING = {
    'ق' : 'Q',
    'ن' : 'N',
    'ی' : 'Y',
}

GRAPHEMES = "".join(RASM_MAPPING.keys())
VOWELS = 'ًٌٍَُِ'
#VOWELS = 'ًࣰٌࣱٍࣲَُِّْۣۭۡٓۜۢ۟۠ۖۗۘۙۚۛ'

NORM_REGEX = re.compile('|'.join(NORM_MAPPING))
CLEAN_REGEX = re.compile(f'[^{GRAPHEMES}]')

RASM_REGEX = re.compile('|'.join(RASM_MAPPING))
QNY_RASM_REGEX = re.compile('(%s)(?=$)' % '|'.join(QNY_RASM_MAPPING))

def prepare_quran(quranfp):
    """ prepare preprocessed tanzil quran for the quran tagger.

    Args:
        quranfp (io.TextIOWrapper): pointer to preprocessed quran.

    Return:
        dict: 2-element structure containing the quran:

            "qrasm" : {"BSM": [0, 63, ...], "LLH" : [...], ...},
            "qtext" : [((1,1,1), ("بِسْمِ", "بِسمِ")), ((1,1,2), ("ٱللَّهِ", "للَهِ")), ...]
            "sura_names" : {"name": [start_offset, end_offset], ...} 

    """
    sura_names = {"الفَاتِحَة": 1, "أم الكتاب": 1, "أم القرآن": 1, "السبع المثاني": 1,
                  "الحمد": 1, "الشفاء": 1, "البَقَرَة": 2, "آل عِمرَان": 3, "النِّسَاء": 4,
                  "المَائدة": 5, "الأنعَام": 6, "الأعرَاف": 7, "الأنفَال": 8, "التوبَة": 9,
                  "براءة": 9, "يُونس": 10, "هُود": 11, "يُوسُف": 12, "الرَّعْد": 13,
                  "إبراهِيم": 14, "الحِجْر": 15, "النَّحْل": 16, "الإسْرَاء": 17,
                  "بَنِي إِسرائيل": 17, "الكهْف": 18, "مَريَم": 19, "طه": 20,
                  "الأنبيَاء": 21, "الحَج": 22, "المُؤمنون": 23, "النُّور": 24,
                  "الفُرْقان": 25, "الشُّعَرَاء": 26, "النَّمْل": 27, "القَصَص": 28,
                  "العَنكبوت": 29, "الرُّوم": 30, "لقمَان": 31, "السَّجدَة": 32,
                  "الأحزَاب": 33, "سَبَأ": 34, "فَاطِر": 35, "يس": 36, "الصَّافات": 37,
                  "ص": 38, "الزُّمَر": 39, "غَافِر": 40, "المُؤْمِن": 40, "فُصِّلَتْ": 41,
                  "حم سجدة": 41, "الشُّورَى": 42, "الزُّخْرُف": 43, "الدخَان": 44,
                  "الجَاثيَة": 45, "الأحْقاف": 46, "محَمَّد": 47, "الفَتْح": 48, "الحُجرَات": 49,
                  "ق": 50, "الذَّاريَات": 51, "الطُّور": 52, "النَّجْم": 53, "القَمَر": 54,
                  "الرَّحمن": 55, "الوَاقِعَة": 56, "الحَديد": 57, "المجَادلة": 58, "الحَشر": 59,
                  "المُمتَحنَة": 60, "الصَّف": 61, "الجُمُعَة": 62, "المنَافِقون": 63, "التغَابُن": 64,
                  "الطلَاق": 65, "التحْريم": 66, "المُلْك": 67, "تَبَارَكَ": 67, "القَلَم": 68,
                  "الحَاقَّة": 69, "المعَارج": 70, "نُوح": 71, "الجِن": 72, "المُزَّمِّل": 73,
                  "المُدَّثِّر": 74, "القِيَامَة": 75, "الإنسَان": 76, "المُرسَلات": 77, "النَّبَأ": 78,
                  "النّازعَات": 79, "عَبَس": 80, "التَّكوير": 81, "الانفِطار": 82, "المطفِّفِين": 83,
                  "الانْشِقَاق": 84, "البرُوج": 85, "الطَّارِق": 86, "الأَعْلى": 87, "الغَاشِية": 88,
                  "الفَجْر": 89, "البَلَد": 90, "الشَّمْس": 91, "الليْل": 92, "الضُّحَى": 93,
                  "الشَّرْح": 94, "التِّين": 95, "العَلَق": 96, "القَدْر": 97, "البَينَة": 98,
                  "الزلزَلة": 99, "العَادِيات": 100, "القَارِعة": 101, "التَّكَاثر": 102,
                  "العَصْر": 103, "الهُمَزَة": 104, "الفِيل": 105, "قُرَيْش": 106, "المَاعُون": 107,
                  "الكَوْثَر": 108, "الكَافِرُون": 109, "النَّصر": 110, "المَسَد": 111, "الإخْلَاص": 112,
                  "الفَلَق": 113, "النَّاس": 114}

    sura_names = {normalise(k) : v for k, v in sura_names.items()}
    qrasm, qtext, i, sura_start, prev_isura = {}, [], -1, 0, 0

    entries = (li.split('|', 2) for li in filter(None, (l.strip() for l in quranfp)) if not li[0]=='#')

    for sura, vers, text in entries:
        isura = int(sura)
        ivers = int(vers)

        for iword, word in enumerate(text.split(), 1):
            word_norm = normalise(word)
            word_rasm = rasm(word_norm)

            qtext.append(((isura, ivers, iword), (word, word_norm)))
            qrasm[word_rasm] = qrasm.get(word_rasm, [])+[i:=i+1]

            if isura != prev_isura:
                for sn in [k for k, v in sura_names.items() if v == prev_isura]:
                    sura_names[sn] = [sura_start, i-1]
                sura_start = i
                prev_isura = isura

    return {'qrasm': qrasm, 'qtext': qtext, 'sura_names': sura_names}

def prepare_stopwords(quranfp):
    """ prepare preprocessed tanzil quran for the quran tagger.

    Args:
        quranfp (io.TextIOWrapper): pointer to processed leeds quran.

    Return:
        dict: rasmised stopwords as keys and list of corresponding normalised stopwords as values. 

            {"W": ["و"], "BY": ["یی", "نی", "بی"], ...}

    """
    quran_words = {}
    for ind, group in groupby(json.load(quranfp), key=lambda x: (x['sura'], x['vers'], x['word'])):
        group = list(group)
        token = ''.join(g['tok'] for g in group)
        token_norm = normalise(token)
        token_rasm = rasm(token_norm)
        pos_list = tuple(g['POS'] for g in group)
        quran_words[pos_list] = quran_words.get(pos_list, set()).union({(token_rasm, token_norm)})

    rasm_norm_words = set()
    for pos_list, norm_words in quran_words.items():
        if pos_list in (('PRON',), ('REL',), ('NEG',), ('P',), ('CONJ',), ('SUB',), ('INTG',), ('AVR',), ('CONJ', 'PRON'), ('P', 'PRON'), ('CONJ', 'NEG'),
            ('CONJ', 'REL'), ('P', 'REL'), ('CONJ', 'P'), ('REM', 'P', 'REL'), ('SUP', 'AMD'), ('REM', 'COND'), ('INTG', 'T')):
            rasm_norm_words = rasm_norm_words.union(norm_words)

    stopwords = {}
    for rasm_tok, norm_tok in sorted(rasm_norm_words, key=lambda x: len(x[0])):
        stopwords[rasm_tok] = stopwords.get(rasm_tok, set()).union((norm_tok,))

    #for rasm_tok, norm_list in stopwords.items():
    #    print(rasm_tok, norm_list)

    for k in stopwords:
        stopwords[k] = list(stopwords[k])

    return stopwords

def normalise(s, rm_conj=True):
    """ normalise Arabic script.

    Args:
        s (str): Arabic-scripted text to normalise.
        rm_conj (bool): remove all initial waw and fa and it's following vowel.
            They might be possible conjunctions.

    Return:
        str: normalised text.

    """
    s = NORM_REGEX.sub(lambda m: NORM_MAPPING[m.group(0)], s)
    s = CLEAN_REGEX.sub('', s)
    if rm_conj and len(s)>1 and (s[0]=='و' or s[0]=='ف'):
        s = s[1:]
    return s.replace('ا', '')

def rasm(s):
    """ convert s to archigraphemic representation.

    Args:
        s (str): text to rasmise.

    Return:
        s: rasmised text.

    """
    s = QNY_RASM_REGEX.sub(lambda m: QNY_RASM_MAPPING[m.group(0)], s)
    return RASM_REGEX.sub(lambda m: RASM_MAPPING[m.group(0)], s)
    

AL_SURA = [rasm(normalise(el)) for el in ["السورة", "الآيات"]]  #  , "الآي"]]
KULLAHA = rasm(normalise("كلها"))
AYA = [rasm(normalise(el)) for el in ["آية", "آيات", "آيتين"]]
AL_AYA = [rasm(normalise(el)) for el in ["الآية", "الآيات", "الآيتين"]]  #, "الآي"]]
SURA = rasm(normalise("سورة"))
sura_names1 = "الفَاتِحَة,,أم,السبع,الحمد,الشفاء,البَقَرَة,آل,النِّسَاء,المَائدة,الأنعَام,الأعرَاف,الأنفَال,التوبَة,براءة,يُونس,هُود,يُوسُف,الرَّعْد,إبراهِيم,الحِجْر,النَّحْل,الإسْرَاء,بَنِي,الكهْف,مَريَم,طه,الأنبيَاء,الحَج,المُؤمنون,النُّور,الفُرْقان,الشُّعَرَاء,النَّمْل,القَصَص,العَنكبوت,الرُّوم,لقمَان,السَّجدَة,الأحزَاب,سَبَأ,فَاطِر,يس,الصَّافات,ص,الزُّمَر,غَافِر,المُؤْمِن,فُصِّلَتْ,حم,الشُّورَى,الزُّخْرُف,الدخَان,الجَاثيَة,الأحْقاف,محَمَّد,الفَتْح,الحُجرَات,ق,الذَّاريَات,الطُّور,النَّجْم,القَمَر,الرَّحمن,الوَاقِعَة,الحَديد,المجَادلة,الحَشر,المُمتَحنَة,الصَّف,الجُمُعَة,المنَافِقون,التغَابُن,الطلَاق,التحْريم,المُلْك,تَبَارَكَ,القَلَم,الحَاقَّة,المعَارج,نُوح,الجِن,المُزَّمِّل,المُدَّثِّر,القِيَامَة,الإنسَان,المُرسَلات,النَّبَأ,النّازعَات,عَبَس,التَّكوير,الانفِطار,المطفِّفِين,الانْشِقَاق,البرُوج,الطَّارِق,الأَعْلى,الغَاشِية,الفَجْر,البَلَد,الشَّمْس,الليْل,الضُّحَى,الشَّرْح,التِّين,العَلَق,القَدْر,البَينَة,الزلزَلة,العَادِيات,القَارِعة,التَّكَاثر,العَصْر,الهُمَزَة,الفِيل,قُرَيْش,المَاعُون,الكَوْثَر,الكَافِرُون,النَّصر,المَسَد,الإخْلَاص,الفَلَق,النَّاس,".split(",")
SURA_NAMES1 = [rasm(normalise(el)) for el in sura_names1]
sura_names2 = "القرآن,الكتاب,المثاني,عِمرَان,إِسرائيل,سجدة".split(",")
SURA_NAMES2 = [rasm(normalise(el)) for el in sura_names2]
ILA = rasm(normalise("إلى"))
HATTA = rasm(normalise("حتى"))
IDHA = rasm(normalise("إذا"))
END_NOUN = [rasm(normalise(el)) for el in ["آخر", "تمام", "خاتمة"]]
END_NOUN_HA = [rasm(normalise(el)) for el in ["آخرها", "تمامها", "خاتمتها"]]
AN = rasm(normalise("أن"))
end_verbs1 = "ختم,ختمت,تختم,تختمت,انقضت,تنقضي,أتم".split(",")
END_VERB1 = [rasm(normalise(el)) for el in end_verbs1]
END_VERB1_HA = [rasm(normalise(el+"ها")) for el in end_verbs1]
end_verbs2 = "فرغ,فرغت,يفرغ".split(",")
END_VERB2 = [rasm(normalise(el)) for el in end_verbs2]
MIN = rasm(normalise("من"))
MINHA = rasm(normalise("منها"))
ALKH = rasm(normalise("الخ"))
QAWL = rasm(normalise("قول"))
QAWLIHI = rasm(normalise("قوله"))
god_epithets = "تعالى,سبحانه,عز,جل,تبارك".split(",")
GOD = [rasm(normalise(el)) for el in god_epithets] + [rasm(normalise("الله"))]
WA_GOD = [rasm(normalise("و"+el)) for el in god_epithets]
god_attributes = "ذكره,شأنه,اسمه".split(",")
GOD_ATTRIBUTES = [rasm(normalise(el)) for el in god_attributes]
AKHIR = rasm(normalise("آخر"))
AKHIRHA = rasm(normalise("آخرها"))
to_verbs_cala = "أتى,أتيت,يأتي".split(",")
TO_VERB_CALA = [rasm(normalise(el)) for el in to_verbs_cala]
to_verbs_ila = "انتهى,انتهت,بلغ,بلغت".split(",")
TO_VERB_ILA = [rasm(normalise(el)) for el in to_verbs_ila]
CALA = rasm(normalise("على"))
ILA = rasm(normalise("إلى"))
speech_verbs = "قال,قالت,قلت,قرأ,قرأت".split(",")
SPEECH_VERB = [rasm(normalise(el)) for el in speech_verbs]


def check_ellipsis(words_rasm, i, size=None, debug=False):
    """Check whether the Quran quotation is an elliptical quotation
    (that is, if it is not quoted fully but abbreviated by quoting
    only the start and end of the intended quotation).
    
    Examples:
        - قرأ رسول الله صلى الله عليه وسلم فأما من أعطى واتقى وصدق بالحسنى *** إلى قوله *** فسنيسره للعسرى
        - فأنزل الله تعالى تبت يدا أبي لهب وتب *** إلى آخرها 
        - الآية التي في البقرة قولوا آمنا بالله وما أنزل إلينا *** إلى آخر الآية

    Args:
        words_rasm (list(tuple)): contains a tuple for each token in the text:
            (its_raw_form, its_normalized_form, its_rasmised_form)
        i (int): token index after the end token of the Qur'an quotation in the text
        size (int): size of words_rasm.
    """
    if not size:
        size = len(words_rasm)
    ell = ""
    try:
        if debug:
            print(f"start (ellipsis): i={i}, words_rasm[i][2]={words_rasm[i][2]}, size-1={size-1}", file=sys.stderr) #TRACE
        # AYA/SURA:
        if words_rasm[i][2] in AL_SURA:
            ell += "al_sura "
            i += 1
            if i <= size-1 and words_rasm[i][2] == KULLAHA:
                ell += "kullaha"
                return ell
        elif words_rasm[i][2] in AYA:
            ell += "aya "
            i += 1
        elif words_rasm[i][2] in AL_AYA:
            ell += "al_aya "
            i += 1
            if i <= size-1 and words_rasm[i][2] == KULLAHA:
                ell += "kullaha"
                return ell
        if words_rasm[i][2] == SURA:
            ell += "surat "
            i += 1
        if words_rasm[i][2] in SURA_NAMES1:
            ell += "sura_name1 "
            i += 1
            if i <= size-1:
                if words_rasm[i][2] in SURA_NAMES2:
                    ell += "sura_name2 "
                    i += 1
        # UNTIL:
        if words_rasm[i][2] == ALKH:  # الخ : abbreviation for ila akhirihi/ha
            ell += "ila end_noun_ha"
            return ell
        elif words_rasm[i][2] in [ILA, HATTA]:
            if words_rasm[i][2] == ILA:
                ell += "ila "
            else:
                ell += "hatta "
            i += 1

            if i <= size-1:
                # END_NOUN: 
                if words_rasm[i][2] in END_NOUN_HA:
                    ell += "end_noun_ha"
                    r = True
                    return ell
                elif words_rasm[i][2] in END_NOUN:
                    ell += "end_noun "
                    i += 1
                    if i <= size-1:
                        if words_rasm[i][2] in AL_SURA+AL_AYA:
                            if words_rasm[i][2] in AL_SURA:
                                ell += "al_sura "
                            else:
                                ell += "al_aya "
                            i += 1
                            if i <= size-1:
                                if words_rasm[i][2] == KULLAHA:
                                    ell += "kullaha"
                            return ell.strip()
                        if words_rasm[i][2] in SURA:
                            ell += "surat "
                            i += 1
                        if i <= size-1:
                            if words_rasm[i][2] in SURA_NAMES1:
                                ell += "sura_name1 "
                                i += 1
                                if i <= size-1:
                                    if words_rasm[i][2] in SURA_NAMES2:
                                        ell += "sura_name2 "
                                        i += 1
                        return ell.strip()
                    
                # END_VERB/TO_VERB/SPEECH_VERB:
                if words_rasm[i][2] == AN:
                    ell += "an "    
                    i += 1
                if ("hatta" in ell or "ila an" in ell):
                    if i <= size-1 and words_rasm[i][2] == IDHA:
                        ell += "idha "
                        i += 1
                    if i <= size-1:
                        if words_rasm[i][2] in END_VERB1_HA:
                            ell += "end_verb_ha"
                            return ell
                        elif words_rasm[i][2] in END_VERB1+END_VERB2:
                            ell += "end_verb "
                            i += 1
                            if i <= size-1:
                                if words_rasm[i-1][2] in END_VERB2:
                                    if words_rasm[i][2] == MIN:
                                        ell += "min "
                                        i += 1
                                    elif words_rasm[i][2] == MINHA:
                                        ell += "min_ha"
                                        return ell
                                if i <= size-1:
                                    if words_rasm[i][2] in AL_SURA+AL_AYA:
                                        if words_rasm[i][2] in AL_SURA:
                                            ell += "al_sura "
                                        else:
                                            ell += "al_aya "
                                        i += 1
                                if i <= size-1:
                                    if words_rasm[i][2] == KULLAHA:
                                        ell += "kullaha"
                                        return ell.strip()
                                    if words_rasm[i][2] in END_NOUN_HA:
                                        ell += "end_noun_ha"
                                        return ell
                                    elif words_rasm[i][2] in SURA:
                                        ell += "surat "
                                        i += 1
                                    if i <= size-1:
                                        if words_rasm[i][2] in SURA_NAMES1:
                                            ell += "sura_name1 "
                                            i += 1
                                            if i <= size-1:
                                                if words_rasm[i][2] in SURA_NAMES2:
                                                    ell += "sura_name2 "
                                                    i += 1
                            return ell.strip()  # END_VERB only

                        # SPEECH VERBS: ḥattā qāla, ilā an qara'a, ...
                        elif words_rasm[i][2] in SPEECH_VERB:
                            ell += "speech_verb"
                            i+= 1
                            if i <= size-1:
                                if words_rasm[i][2] in GOD:
                                    ell += "GOD "
                                    i += 1
                                    god_end = False
                                    while i <= size-1:
                                        if words_rasm[i][2] in WA_GOD:
                                            ell += "wa_GOD "
                                            i += 1
                                        elif words_rasm[i][2] in GOD_ATTRIBUTES:
                                            ell += "GOD_attribute "
                                            i += 1
                                        else:
                                            break
                            return ell

                        # TO_VERBS: ḥattā intahā ilā, ilā an atā ʿalā, ...
                        elif words_rasm[i][2] in TO_VERB_CALA + TO_VERB_ILA:
                            if i <= size-2:
                                if words_rasm[i][2] in TO_VERB_CALA and words_rasm[i+1][2] == CALA:
                                    ell += "to_verb cala "
                                    i += 2
                                elif words_rasm[i][2] in TO_VERB_ILA and words_rasm[i+1][2] == ILA:
                                    ell += "to_verb ila "
                                    i += 2
                                if i <= size-1:
                                    if words_rasm[i][2] in AL_AYA:
                                        ell += "al_aya"
                                return ell.strip()
    
                # until specific tokens:
                if words_rasm[i][2] in (QAWL, QAWLIHI):
                    if words_rasm[i][2] == QAWLIHI:
                        ell += "qawlihi "
                    else:
                        ell += "qawl "
                    i += 1
                    if i <= size-1:
                        if words_rasm[i][2] in GOD:
                            ell += "GOD "
                            i += 1
                            god_end = False
                            while i <= size-1:
                                if words_rasm[i][2] in WA_GOD:
                                    ell += "wa_GOD "
                                    i += 1
                                elif words_rasm[i][2] in GOD_ATTRIBUTES:
                                    ell += "GOD_attribute "
                                    i += 1
                                else:
                                    break
                    if not ell.endswith("qawl "):
                        return ell.strip()
        try:
            return re.findall("ila|hatta", ell)[0]
        except:
            return False
    except IndexError:
        return False

def last_token_of_sura_or_aya(qtext, start, n, n_type):
    """Find the end of a sura or verse.

    Args:
        qtext (list): list that contains for every token in the Quran
            two tuples: ((token, normalized_token), (sura_no, aya_no, word_no))
        start (int): token index of a token in the verse
        n (int): aya or sura number
        n_type (str): "aya" or "sura"
        
    Returns:
        int : (zero-based) token index of the last token in the current sura/aya in the Quran
    """
    t = {"sura": 0, "aya": 1}[n_type]
    i = 0
    end = False
    size = len(qtext)
    while not end and qtext[start+i][0][t] == n:
        i += 1
        if start + i == size:
            end = True
    return start + i - 1

if __name__ == '__main__':

    parser = ArgumentParser(description='prepare tanzil quran for tagger')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare_quran', action='store_true', help='create the quran struct')
    group.add_argument('--prepare_stopwords', action='store_true', help='get list of stopword')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='preprocessed tanzil quran')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='prepared tanzil quran')
    args = parser.parse_args()

    if args.prepare_quran:
        json.dump(prepare_quran(args.infile), args.outfile)

    elif args.prepare_stopwords:
        json.dump(prepare_stopwords(args.infile), args.outfile)

