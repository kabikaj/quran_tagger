#!/usr/bin/env python3
#
#    util.py
#
# utility functions for quran_tagger.py
#
# requirements:
#   * quran-uthmani.json
#
# usage:
#   $ cat quran-uthmani.json | python util.py --prepare_quran > quran.json
#
##########################################################################

import re
import sys
import ujson as json
from argparse import ArgumentParser, FileType


NORM_MAPPING = {
    'ࣱ' : 'ٌ',
    'ُُ' : 'ٌ',
    'ࣰ' : 'ً',
    'ََ' : 'ً',
    'ࣲ' : 'ٍ',
    'ِِ' : 'ٍ',
    'ة' : 'ه',
    'ہ' : 'ه',
    'ھ' : 'ه',
    'ﻫ' : 'ه',
    #'إ' : 'ا',
    #'أ' : 'ا',
    #'آ' : 'ا',
    #'ٱ' : 'ا',
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

CONJ_REGEX = re.compile('^[وف][َُِ]?')
NORM_REGEX = re.compile('|'.join(NORM_MAPPING))
CLEAN_NORM_REGEX = re.compile(f'[^{GRAPHEMES}{VOWELS}]')

RASM_REGEX = re.compile('|'.join(RASM_MAPPING))
CLEAN_RASM_REGEX = re.compile(f'[^{GRAPHEMES}]')
QNY_RASM_REGEX = re.compile('(%s)(?=$)' % '|'.join(QNY_RASM_MAPPING))

EXPANDED_REGEX = re.compile(fr'([^{VOWELS}])(?![{VOWELS}])')

def normalise(s, rm_conj=True):
    """ normalise Arabic script.

    Args:
        s (str): Arabic-scripted text to normalise.
        rm_conj (bool): remove all initial waw and fa and it's following vowel.
            They might be possible conjunctions.

    Return:
        str: normalised text.

    """
    if rm_conj and len(s)>3:
        s = CONJ_REGEX.sub('', s)
    norm_s = NORM_REGEX.sub(lambda m: NORM_MAPPING[m.group(0)], s)
    return CLEAN_NORM_REGEX.sub('', norm_s)

def rasm(s):
    """ convert s to archigraphemic representation.

    Args:
        s (str): text to rasmise.

    Return:
        s: rasmised text.

    """
    clean_s = CLEAN_RASM_REGEX.sub('', s)
    rasm_s = QNY_RASM_REGEX.sub(lambda m: QNY_RASM_MAPPING[m.group(0)], clean_s)
    return RASM_REGEX.sub(lambda m: RASM_MAPPING[m.group(0)], rasm_s)

def equal(textA, textB):
    """ check if Arabic-scripted textA and textB should be considered the same.
    TextB if fully vowelled, whereas textA can contain complete, partial or no vowels.

    Args:
        textA (str): first text to compare.
        textB (str): second text to compare.

    Return:
        bool: True if both takes are considered the same, False otherwise.

    """
    textA_expanded = EXPANDED_REGEX.sub(fr'\1[{VOWELS}]*', textA)
    return True if re.match(textA_expanded, textB) else False

def prepare_quran(pre_quran):
    """ prepare preprocessed tanzil quran for the quran tagger.

    Args:
        pre_quran (io.TextIOWrapper): pointer to preprocessed quran.

    Return:
        dict: 3-element structure containing the quran

            "qtext" : [(1,1,1), (1,1,2), (1,1,2), ...]
            "qrasm" : {"BSM": [0, 63, ...], "LLH" : [...], ...},
            "qword" : {"1": {"1": {"1": ("بِسْمِ", "بِسمِ"), "2": ("ٱللَّهِ", "للَهِ"), ...}, ...}, ...}

    """
    qtext, qrasm, qword, i = [], {}, {}, 0

    for sura in pre_quran:
        isura = int(sura['sura'])
    
        for vers in sura['verses']:
            ivers = int(vers['verse'])
    
            for iword, word in enumerate(vers['full_text'].split(), 1):
                word_norm = normalise(word)
                word_rasm = rasm(word_norm)

                qtext.append((isura, ivers, iword))
                qrasm[word_rasm] = qrasm.get(word_rasm, [])+[i:=i+1]
                
                if isura in qword:
                    if ivers in qword[isura]:
                        if iword not in qword[isura][ivers]:
                            qword[isura][ivers][iword] = (word, word_norm)
                    else:
                        qword[isura][ivers] = {iword : (word, word_norm)}
                else:
                    qword[isura] = {}
                    qword[isura][ivers] = {iword : (word, word_norm)}

    return {'qrasm': qrasm, 'qtext': qtext, 'qword': qword}

if __name__ == '__main__':

    parser = ArgumentParser(description='prepare tanzil quran for tagger')
    parser.add_argument('--prepare_quran', action='store_true', required=True, help='create the quran struct')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='preprocessed tanzil quran')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='prepared tanzil quran')
    args = parser.parse_args()

    json.dump(prepare_quran(json.load(args.infile)), args.outfile)
