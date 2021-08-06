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
import json as old_json
from argparse import ArgumentParser, FileType
import textwrap


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


with open("stopwords.json", mode="r", encoding="utf-8") as file:
    STOP_WORDS = set([rasm(normalise(w)) for w in json.load(file)])


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

def too_common(toks, min_uncommon=1):
    """Check if sequence consists of too many common tokens.

    Args:
        toks (list): list of rasmized tokens
        min_uncommon (int): minimum number of uncommon tokens in the string
            to be considered uncommon

    Returns:
        bool : True if sequence contains at fewer than `min_uncommon` uncommmon tokens
    """
    common = [t in STOP_WORDS for t in toks]
    return common.count(False) < min_uncommon

def prepare_quran(pre_quran):
    """ prepare preprocessed tanzil quran for the quran tagger.

    Args:
        pre_quran (io.TextIOWrapper): pointer to preprocessed quran.

    Return:
        dict: 2-element structure containing the quran:

            "qrasm" : {"BSM": [0, 63, ...], "LLH" : [...], ...},
            "qtext" : [((1,1,1), ("بِسْمِ", "بِسمِ")), ((1,1,2), ("ٱللَّهِ", "للَهِ")), ...]

    """
    qrasm, qtext, i = {}, [], -1

    for sura in pre_quran:
        isura = int(sura['sura'])
    
        for vers in sura['verses']:
            ivers = int(vers['verse'])
    
            for iword, word in enumerate(vers['full_text'].split(), 1):
                word_norm = normalise(word)
                word_rasm = rasm(word_norm)

                qtext.append(((isura, ivers, iword), (word, word_norm)))
                qrasm[word_rasm] = qrasm.get(word_rasm, [])+[i:=i+1]

    return {'qrasm': qrasm, 'qtext': qtext}


ILA = rasm(normalise("إلى"))
QAWL = rasm(normalise("قوله"))
TACALA = rasm(normalise("تعالى"))
AKHIR = rasm(normalise("آخر"))
AKHIRHA = rasm(normalise("آخرها"))
SURA = rasm(normalise("سورة"))
AYA = rasm(normalise("آية"))

def check_ellipsis(words_rasm, i):
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
    """
    r = False
    if i < len(words_rasm)-1 and words_rasm[i][2] == ILA and i+1 < len(words_rasm)-1:
        r = "ila"
        if words_rasm[i+1][2].startswith(QAWL):
            r += " qawl"
            if i+2 < len(words_rasm)-1 and words_rasm[i+2][2] == TACALA:
                r += " tacala"
        elif words_rasm[i+1][2] == AKHIRHA:
            r += " akhirha"
        elif words_rasm[i+1][2] == AKHIR:
            r += " akhir"
            if i+2 < len(words_rasm)-1 and words_rasm[i+2][2] == SURA:
                r += " sura"
            elif i+2 < len(words_rasm)-1 and words_rasm[i+2][2] == AYA:
                r += " aya"
    return r

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
    while not end and qtext[start+i][0][t] == n:
        i += 1
        if start + i == len(qtext):
            end = True
    return start + i - 1

def shorten(s, width=50, placeholder=' [...] '):
    """Shorten a long string to width, keeping text at the beginning and the end."""
    start = textwrap.shorten(s, width=int(width-len(placeholder)/2), placeholder="")
    end = textwrap.shorten(s[::-1], width=int(width-len(placeholder)/2), placeholder="")[::-1]
    return f'        {start}{placeholder}{end}'
    


if __name__ == '__main__':
    fp = "../quran-tag/resources/quranAnalysis_frequent_phrases.tsv"
    with open(fp, mode="r", encoding="utf-8") as file:
        data = [x.split("\t")[0] for x in file.readlines()]
        tok_data = [[rasm(normalise(tok)) for tok in t.split(" ")] for t in data[1:]]
    for i, t in enumerate(tok_data):
        print(too_common(t, 1), data[i+1])

    parser = ArgumentParser(description='prepare tanzil quran for tagger')
    parser.add_argument('--prepare_quran', action='store_true', required=True, help='create the quran struct')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='preprocessed tanzil quran')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='prepared tanzil quran')
    args = parser.parse_args()

    json.dump(prepare_quran(json.load(args.infile)), args.outfile)
