#!/usr/bin/env python3
#
#    quran_tagger.py
#
# tag quranic quotes in text
#
# Authors:
#   Alicia Gonzalez Martinez, InterSaME project, Hamburg University
#   Peter Verkinderen
#
# The Quran tagger uses the tanzil Quran and it uses an archigraphemic representation of letterblocks for Arabic script
# These two concepts have been develoed by Thomas Milo
#
# TODO
#   * have to equals with a flag; one stripping the vowels
#   * add peter to acknowledges
#   * remove the innecesary loops from the test script
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

from util import normalise, rasm, equal

QURAN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quran.json')

with open(QURAN_PATH) as quranfp:
    QURAN = json.load(quranfp)

QURAN['qrasm'] = {k : set(d) for k, d in QURAN['qrasm'].items()}

MIN_BLOCKS = 5

class TokensError(Exception):
    """ Raised when the number of tokens is illogical.

    """
    pass

def tagger(words, qstruct=QURAN, min_blocks=MIN_BLOCKS, rasm_match=False, debug=False):
    """ tag words with quranic quotations.

    Args:
        words (list): text as a list of words.
        qstruct (dict): quran structure.
        min_blocks (int): minimum number of blocks to accept as match.
        rasm (bool): accept pure rasm matches.
        debug (bool): show debugging info.

    Yield:
        int, int, int, int: index to initial word, index to final word, starting quran index, end quran index.

    Exception:
        TokensError: if number of blocks is smaller than 2.

    """
    if min_blocks <= 1:
        raise TokensError('The minimum number of blocks must be at least 2')

    #text = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)] #FIXME
    words_rasm = [rasm(normalise(w)) for w in words]
    end_of_chains = dict()
    nwords = len(words_rasm)

    for i, rasm_tok in enumerate(words_rasm):
        for iquran in qstruct['qrasm'].get(rasm_tok, set()):

            j = 0
            while i+j < nwords-1:
                j += 1
                if not words_rasm[i+j] in qstruct['qrasm'] or not iquran+j in qstruct['qrasm'][words_rasm[i+j]]:
                    break
            if j >= MIN_BLOCKS:
                if not i+j in end_of_chains:
                    end_of_chains[i+j] = {j: [(i, iquran)]}
                elif not j in end_of_chains[i+j]:
                    end_of_chains[i+j][j] = [(i, iquran)]
                else:
                    end_of_chains[i+j][j].append((i, iquran))

    # in case there are several positbilities starting in the same block, take first #FIXME recheck this
    filtered_uniq = {ibloc : (iquran, step) for ibloc, iquran, step in found}
    filtered_uniq = [(ibloc, iquran, step) for ibloc, (iquran, step) in filtered_uniq.items()]

    if not filtered_uniq:
        return

    filtered_longest = [filtered_uniq[0]]
    last_ending = filtered_longest[0][0]+filtered_longest[0][-1]

    for i, (ibloc, iquran, step) in enumerate(filtered_uniq[1:], 1):

        # get longest step and skip succesive smaller ones
        if not (ibloc-1==filtered_uniq[i-1][0] and iquran-1==filtered_uniq[i-1][1] and step+1==filtered_uniq[i-1][2]):

            # do not allow overlaps
            if ibloc < last_ending:
                if step > filtered_longest[-1][-1]:
                    filtered_longest.pop()
                    filtered_longest.append((ibloc, iquran, step))
            else:
                filtered_longest.append((ibloc, iquran, step))

        last_ending = ibloc+step

    for ibloc, iquran, step in filtered_longest:

            text_ini = text_blocks[ibloc][1]
            text_end = text_blocks[ibloc+step][1]

            text_ori = ' '.join((x[0] for x in text_rasm[text_ini:text_end]))
            text_norm = ' '.join((x[1] for x in text_rasm[text_ini:text_end]))

            quran_irange = list(dict.fromkeys(tuple(qstruct['qtext'][iq][:-1]) for iq in range(iquran, iquran+step)))
            
            quran_ori = ' '.join(qstruct['qwords'].get(str(iqs), {}).get(str(iqv), {}).get(str(iqw), {})[0] for iqs, iqv, iqw in quran_irange)
            quran_norm = ' '.join(qstruct['qwords'].get(str(iqs), {}).get(str(iqv), {}).get(str(iqw), {})[1] for iqs, iqv, iqw in quran_irange)

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

