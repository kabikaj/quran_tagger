#!/usr/bin/env python3
#
#    quran_tagger.py
#
# tag quranic quotes in text
#
# Author: Alicia Gonzalez Martinez, InterSaME project, Hamburg University
#
# The Quran tagger uses the tanzil Quran and it uses an archigraphemic representation of letterblocks for Arabic script
# These two concepts have been develoed by Thomas Milo
#
# requirements:
#   * depends on quran.json
#
# performance tests:
#   $ hyperfine "echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ مِنكُمْ وَٱلصَّابِرِينَ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py" --warmup 1
#   $ echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ مِنكُمْ وَٱلصَّابِرِينَ وَنَبْلُوَاْ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python -m cProfile quran_tagger.py
#
# examples:
#   $ python quran_tagger.py --min 2 <(echo '["نرينك","بعض"]')
#   $ echo "نرينك بعض" | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 2
# 
######################################################################################################################################################

import os
import re
import sys
import ujson as json
from argparse import ArgumentParser, FileType

MIN_BLOCKS = 5

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

}

QNY_RASM_MAPPING = {
    'ق$' : 'Q',
    'ن$' : 'N',
    'ی$' : 'Y',
    'ق'  : 'F',
    'ن'  : 'B',
    'ی'  : 'B',
}

GRAPHEMES = f'{"".join(RASM_MAPPING.keys())}قنی'
VOWELS = 'ًٌٍَُِ'

NORM_REGEX = re.compile('|'.join(NORM_MAPPING))
CLEAN_NORM_REGEX = re.compile(f'[^{GRAPHEMES}{VOWELS} ]')

RASM_REGEX = re.compile('|'.join(RASM_MAPPING))
CLEAN_RASM_REGEX = re.compile(f'[^{GRAPHEMES}]')
QNY_RASM_REGEX = re.compile('|'.join(QNY_RASM_MAPPING))
ARDW_RASM_REGEX = re.compile(r'([ARDW])(?!$)')

#EXPAND_REGEX = re.compile(rf'([{GRAPHEMES}])(?=[^{GRAPHEMES}])') #FIXME

class BlocksError(Exception):
    pass

def normalise(s):
    """ normalise Arabic script.

    Args:
        s (str): Arabic-scripted text to normalise.

    Return:
        str: normalised text.

    """
    norm_s = NORM_REGEX.sub(lambda m: NORM_MAPPING[m.group(0)], s)
    return CLEAN_NORM_REGEX.sub('', norm_s)

def rasm(s):
    """ convert s to archigraphemic representation.

    Args:
        s (str): text to rasmise.

    Return:
        s: rasmised text.

    """
    clean_rasm = CLEAN_RASM_REGEX.sub('', s)
    pre_rasm = RASM_REGEX.sub(lambda m: RASM_MAPPING[m.group(0)], clean_rasm)
    qny_rasm = QNY_RASM_REGEX.sub(lambda m: QNY_RASM_MAPPING[m.group(0)], pre_rasm)
    return ARDW_RASM_REGEX.sub(r'\1 ', qny_rasm)

def equal(textA, textB, debug=False):
    """ check if Arabic-scripted textA and textB should be considered the same.

    Args:
        textA (str): first text to compare.
        textB (str): second text to compare.
        debug (bool): show debugging info.

    Return:
        bool: True if both takes are considered the same, False otherwise.

    """
    textA = re.sub('^[{VOWELS}]+', '', textA)
    textA = re.sub('[{VOWELS}]+$', '', textA)
    textB = re.sub('^[{VOWELS}]+', '', textB)
    textB = re.sub('[{VOWELS}]+$', '', textB)

    #textA = EXPAND_REGEX.sub(rf'\1[{VOWELS}]*', textA) #FIXME
    textA_expanded = re.sub('(.)(?!^)', rf'\1[{VOWELS}]*', textA) #DEBUG

    if debug:
        print(f'@DEBUG@  textA_expanded="{textA_expanded}"  textB="{textB}"', file=sys.stderr) #TRACE

    return True if re.match(textA_expanded, textB) else False

def tagger(words, min_blocks=MIN_BLOCKS, quranpath=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quran.json'), rasm_match=False, debug=False):
    """ tag words with quranic quotations.

    Args:
        words (list): text as a list of words.
        min_blocks (int): minimum number of blocks to accept as match.
        quranfp (str): path to quranic struct.
        rasm (bool): accept pure rasm matches.
        debug (bool): show debugging info.

    Yield:
        int, int, int, int: index to initial word, index to final word, starting quran index, end quran index.

    Exception:
        BlocksError: if number of blocks is smaller than 2.

    """
    if min_blocks <= 1:
        raise BlocksError('The minimum number of blocks must be at least 2.')

    with open(quranpath) as quranfp:
        QURAN = json.load(quranfp)

    text_rasm = [(ori, norm, rasm(norm).split()) for ori, norm in ((w, normalise(w)) for w in words)]
    text_blocks = [(bloc, i) for i, (_, _, blocks) in enumerate(text_rasm) for bloc in blocks]

    found = []
    text_size = len(text_blocks)

    for i, (bloc, itext) in enumerate(text_blocks):
        for iquran in QURAN['qblocks'].get(bloc, []):
            step, j = 1, i+1 #FIXME python 3.8
            while j < text_size-1 and iquran+step in QURAN['qblocks'].get(text_blocks[j][0], []):
                step += 1
                j += 1
            if step >= min_blocks:
                found.append((i, iquran, step))

    # in case there are several positbilities starting in the same block, take first #FIXME recheck this
    filtered_uniq = {ibloc : (iquran, step) for ibloc, iquran, step in found}
    filtered_uniq = [(ibloc, iquran, step) for ibloc, (iquran, step) in filtered_uniq.items()]

    if not filtered_uniq:
        return

    filtered_biggest = [filtered_uniq[0]]
    last_ending = filtered_biggest[0][0]+filtered_biggest[0][-1]

    for i, (ibloc, iquran, step) in enumerate(filtered_uniq[1:], 1):

        # get biggest step and skip succesive smaller ones
        if not (ibloc-1==filtered_uniq[i-1][0] and iquran-1==filtered_uniq[i-1][1] and step+1==filtered_uniq[i-1][2]):

            # do not allow overlaps
            if ibloc < last_ending:
                if step > filtered_biggest[-1][-1]:
                    filtered_biggest.pop()
                    filtered_biggest.append((ibloc, iquran, step))
            else:
                filtered_biggest.append((ibloc, iquran, step))

        last_ending = ibloc+step

    for ibloc, iquran, step in filtered_biggest:

            text_ini = text_blocks[ibloc][1]
            text_end = text_blocks[ibloc+step][1]

            text_ori = ' '.join((x[0] for x in text_rasm[text_ini:text_end]))
            text_norm = ' '.join((x[1] for x in text_rasm[text_ini:text_end]))

            quran_irange = list(dict.fromkeys(tuple(QURAN['qtext'][iq][:-1]) for iq in range(iquran, iquran+step)))
            
            quran_ori = ' '.join(QURAN['qwords'].get(str(iqs), {}).get(str(iqv), {}).get(str(iqw), {})[0] for iqs, iqv, iqw in quran_irange)
            quran_norm = ' '.join(QURAN['qwords'].get(str(iqs), {}).get(str(iqv), {}).get(str(iqw), {})[1] for iqs, iqv, iqw in quran_irange)

            if debug:
                print(f'\n@DEBUG@ ini={text_ini}  end={text_end}  ori="{text_ori}"  norm="{text_norm}"', file=sys.stderr) #TRACE
                print(f'@DEBUG@qini={quran_irange[0]}  qend{quran_irange[-1]} range={quran_irange} qori="{quran_ori}" qnorm="{quran_norm}"', file=sys.stderr) #TRACE

            if rasm_match:
                yield (text_ini, text_end), (quran_irange[0], quran_irange[-1])

            elif equal(text_norm, quran_norm, debug=debug):
                yield (text_ini, text_end), (quran_irange[0], quran_irange[-1])


if __name__ == '__main__':

    parser = ArgumentParser(description='tag text with Quranic quotations')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='tokenised words to tag in json format')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='quranic indexes found')
    parser.add_argument('--min', type=int, default=MIN_BLOCKS, help='minimum number of blocks to accept as a match (at least 2)')
    parser.add_argument('--rasm', action='store_true', help='accept pure rasm matches')
    parser.add_argument('--debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    words = json.load(args.infile)

    for (ini_word, end_word), (ini_quran, end_quran) in tagger(words, min_blocks=args.min, rasm_match=args.rasm, debug=args.debug):
        print(f'Found! ini_word={ini_word} end_word={end_word} ini_quran={ini_quran} end_quran={end_quran}', file=args.outfile)

