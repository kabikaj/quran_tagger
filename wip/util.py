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
#   $ cat quran-simple.txt | python util.py --prepare_quran > quran_simple.json
#   $ cat quran-uthmani.txt | python util.py --prepare_quran > quran_uthmani.json
#   $ cat qc_quran.json | python util.py --prepare_stopwords > stopwords2.json
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
    if len(s)>1 and (s[0]=='و' or s[0]=='ف'):
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


def prepare_quran(quranfp):
    """ prepare preprocessed tanzil quran for the quran tagger.

    Args:
        quranfp (io.TextIOWrapper): pointer to preprocessed quran.

    Return:
        dict: 2-element structure containing the quran:

            "qrasm" : {"BSM": [0, 63, ...], "LLH" : [...], ...},
            "qtext" : [((1,1,1), ("بِسْمِ", "بِسمِ")), ((1,1,2), ("ٱللَّهِ", "للَهِ")), ...]

    """
    qrasm, qtext, i = {}, [], -1

    entries = (li.split('|', 2) for li in filter(None, (l.strip() for l in fpquran)) if not li[0]=='#')

    for sura, vers, text in entries:
        isura = int(sura)
        ivers = int(vers)

        for iword, word in enumerate(text.split(), 1):
            word_norm = normalise(word)
            word_rasm = rasm(word_norm)

            qtext.append(((isura, ivers, iword), (word, word_norm)))
            qrasm[word_rasm] = qrasm.get(word_rasm, [])+[i:=i+1]

    return {'qrasm': qrasm, 'qtext': qtext}


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

