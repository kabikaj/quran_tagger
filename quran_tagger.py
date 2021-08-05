#!/usr/bin/env python3
#
#    quran_tagger.py
#
# tag quranic quotes in text
#
# Authors:
#   Alicia Gonzalez Martinez, InterSaME project, Hamburg University
#   Peter Verkinderen, KITAB project, Aga Khan University
#
# The Quran tagger uses the tanzil Quran and the concept of archigraphemes develoed by Thomas Milo
#
# requirements:
#   * depends on quran.json
#
# performance tests:
#   $ hyperfine "echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ مِنكُمْ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py" --warmup 1
#   $ echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ مِنكُمْ وَٱلصَّابِرِينَ وَنَبْلُوَاْ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python -m cProfile quran_tagger.py --min 3
#
# examples:
#   $ python quran_tagger.py --min 2 <(echo '["نرينك","بعض"]')
#   $ echo "نرينك بعض" | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 2
# 
##########################################################################################################################################################

import os
import re
import sys
import ujson as json
from argparse import ArgumentParser, FileType
from pprint import pprint #DEBUG

from util import normalise, rasm, equal, too_common

QURAN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quran.json')

RED='\033[1;31m'
RESET='\033[0m'

with open(QURAN_PATH) as quranfp:
    QURAN = json.load(quranfp)

QURAN['qrasm'] = {k : set(d) for k, d in QURAN['qrasm'].items()}

MIN_TOKENS = 5

class TokensError(Exception):
    """ Raised when the number of tokens is illogical.

    """
    pass

def tagger(words, qstruct=QURAN, min_tokens=MIN_TOKENS, rasm_match=False, debug=False,
           min_uncommon=0, safe_length=4):
    """ tag words with quranic quotations.

    Args:
        words (list): text as a list of words.
        qstruct (dict): quran structure.
        min_tokens (int): minimum number of tokens to accept as match.
        rasm (bool): accept pure rasm matches.
        debug (bool): show debugging info.
        min_uncommon (int): minimum number of uncommon words to accept as match. 
        safe_length (int): minimum number of tokens to accept as match without
            taking min_uncommon into account.

    Yields:
        tuple: ((int, int), list): index to initial word in the text, index to final word in the text, list of identified quran sequences:
                [ (qindex_ini, qindex_end, quran_ini, quran_end), ...]
                - qindex_ini and qindex_end are lists: [sura_number (int), aya_number (int), word_in_aya_index (int)]
                - quran_ini (int) and quran_end (int) are token offsets of the start and end of the quotation in the Quran
                NB: to access the results:
                for (text_ini, text_end), quran_ids in tagger(words): 
                    for qindex_ini, qindex_end, quran_ini, quran_end in quran_ids:
                        for sura_no, aya_no, token_no in qindex_ini: ...

    Exception:
        TokensError: if number of blocks is smaller than 2.

    """
    if min_tokens <= 0:
        raise TokensError('The minimum number of blocks must be at least 1')

    words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
    end_of_chains = dict() # { index_end_text : { num_tokens_match : [(index_ini_text, index_ini_quran), ...], ... }
    nwords = len(words_rasm)

    for i, (_, norm_tok, rasm_tok) in enumerate(words_rasm):

        # stop searching when the remaining tokens are smaller than the minimum number of accepted tokens
        if i > nwords-min_tokens:
            break

        for iquran in qstruct['qrasm'].get(rasm_tok, set()):
            j = 0
            while i+j < nwords-1:
                j += 1
                if not words_rasm[i+j][2] in qstruct['qrasm'] or not iquran+j in qstruct['qrasm'][words_rasm[i+j][2]]:
                    break
            #print(f'{RED}PREEEEE i={i}  j={j}  min_tokens={min_tokens}  i+j={i+j}  iquran={iquran}{RESET}', file=sys.stderr) #DEBUG
            if j >= min_tokens:
                j -= 1  # j = number of tokens in chain, i + j - 1 is the index position of the last token in the chain!
                #print(f'{RED}<<>> i={i}  j={j}  min_tokens={min_tokens}  i+j={i+j}  iquran={iquran} {words_rasm[i+j-1][2]}{RESET}', file=sys.stderr) #DEBUG
                if not i+j in end_of_chains:
                    end_of_chains[i+j] = {j: [(i, iquran)]}
                elif not j in end_of_chains[i+j]:
                    end_of_chains[i+j][j] = [(i, iquran)]
                else:
                    end_of_chains[i+j][j].append((i, iquran))
                #print(i+j, [k for k in end_of_chains[i+j].keys()])

    #print(f'{RED}end_of_chains', end='    = ', file=sys.stderr) #DEBUG
    #pprint(end_of_chains, stream=sys.stderr) #DEBUG
    #print(f'{RESET}', end='', file=sys.stderr) #DEBUG

    # keep only the longest token chain(s) for each endpoint:
    filtered_longest = dict()
    for end_i in end_of_chains.keys():
        m = max(end_of_chains[end_i].keys())
        filtered_longest[end_i] = end_of_chains[end_i][m]

    #print(f'{RED}filtered_longest', end=' = ', file=sys.stderr) #DEBUG
    #pprint(filtered_longest, stream=sys.stderr) #DEBUG
    #print(f'{RESET}', end='', file=sys.stderr) #DEBUG

    # filter out overlapping chains:
    keys = sorted(filtered_longest.keys(), reverse=True)
    for i, end in enumerate(keys):
        if end in filtered_longest:  # may have been filtered out already!
            start = filtered_longest[end][0][0]
            if i < len(keys)-1:
                prev_end = keys[i+1]
                if not prev_end in filtered_longest:
                    continue
                prev_start = filtered_longest[prev_end][0][0]
                if prev_end > start:
                    if (end - start) > (prev_end - prev_start):
                        filtered_longest.pop(prev_end, None)
                    elif (end - start) < (prev_end - prev_start):
                        filtered_longest.pop(end, None)
                    else:
                        # what to do if overlapping parts have same length? Currently nothing is done...
                        print("overlap Quran quotations with same length: {}-{} vs {}-{}".format(start, end, prev_start, prev_end))

    # filter out short sequences that consist (almost) entirely of common tokens
    # if the sequence is shorter than a specified `safe_length`:
    if min_uncommon:
        filtered_common = dict()
        for text_end, starts in sorted(filtered_longest.items()):
            if starts:
                text_ini = starts[0][0]
                if 1 + text_end - text_ini >= safe_length:
                    filtered_common[text_end] = starts
                else:
                    rasm_toks = (x[2] for x in words_rasm[text_ini:text_end+1])
                    if too_common(rasm_toks, min_uncommon):
                        if debug:
                            text_ori = ' '.join((x[0] for x in words_rasm[text_ini:text_end+1]))
                            print(f'{RED}@DEBUG@ "{text_ori}" discarded because it is too common {RESET}', file=sys.stderr)
                    else:
                        filtered_common[text_end] = starts
    else:
        filtered_common = filtered_longest

    # output:
    for text_end, starts in sorted(filtered_common.items()):
        if starts:
            text_ini = starts[0][0]
            text_norm = ' '.join((x[1] for x in words_rasm[text_ini:text_end+1]))
            if debug:
                text_ori = ' '.join((x[0] for x in words_rasm[text_ini:text_end+1]))
                print(f'{RED}@DEBUG@ ini={text_ini}  end={text_end}\n        ori="{text_ori}"  norm="{text_norm}"', file=sys.stderr) #TRACE

            # group all Qur'anic sequences that end at this token in the text:
            quran_ids = []  
            for text_ini, quran_ini in sorted(starts, key=lambda x: x[1]):
                quran_end = quran_ini + (text_end - text_ini)
                quran_norm = ' '.join(w[1] for _, w in qstruct['qtext'][quran_ini:quran_end+1])

                # last filtering:
                if rasm_match or equal(text_norm, quran_norm):
                    qindex_ini = qstruct['qtext'][quran_ini][0]
                    qindex_end = qstruct['qtext'][quran_end][0]
                    quran_ids.append((qindex_ini, qindex_end, quran_ini, quran_end))

                    if debug:
                        quran_ori = ' '.join(w[0] for _, w in qstruct['qtext'][quran_ini:quran_end+1])
                        print(f'@DEBUG@ qini={quran_ini}  qend={quran_end}\n        qori="{quran_ori}"  qnorm="{quran_norm}"', file=sys.stderr) #TRACE
            if debug:
                print(f'{RESET}', file=sys.stderr) #TRACE

            if quran_ids:
                yield (text_ini, text_end), quran_ids


if __name__ == '__main__':

##    test = "ضصث شس ضكصت هضقأيشب بسم الله الرحمن الرحيم شكث شكتثش"              # no ellipsis
##    test = "ضصث شس ضكصت هضقأيشب بسم الله الرحمن الرحيم إلى مستقيما شكث شكتثش"  # until 1 specified token
    test = "ضصث شس ضكصت هضقأيشب بسم الله الرحمن الرحيم إلى إن الله بكل شكث شكتثش" # until 3 specified tokens
##    test = "ضصث شس ضكصت هضقأيشب بسم الله الرحمن الرحيم إلى إخرها شكث شكتثش"    # until end of sura
##    test =
##    test = "نننننش كصصكككككك شسيبشسيبشسيبشسيبش كنتكنتكتكنتكمنت  كمنتكنمتكمنتكمنت"  # bogus text, no results

    words = re.split(" +", test)
    print("words:")
    for i, w in enumerate(words):
        print(i, w)
##    for (ini, end), quran_ids in tagger(words, debug=True, min_tokens=2, rasm_match=True, min_uncommon=1):
##        print(ini)
##        for qindex_ini, qindex_end, quran_ini, quran_end in quran_ids:
##            print(">", qindex_ini)
##    input("CONTINUE?")
    results = [m for m in tagger(words, debug=True, min_tokens=2, rasm_match=False, min_uncommon=1)]
    print(results)


    parser = ArgumentParser(description='tag text with Quranic quotations')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='tokenised words to tag in json format')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='quranic indexes found')
    parser.add_argument('--min', type=int, default=MIN_TOKENS, help='minimum number of blocks to accept as a match (at least 2)')
    parser.add_argument('--rasm', action='store_true', help='accept pure rasm matches')
    parser.add_argument('--debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    words = json.load(args.infile)

    for (ini_word, end_word), (ini_quran, end_quran) in tagger(words, min_tokens=args.min, rasm_match=args.rasm, debug=args.debug):
        print(f'Found! ini_word={ini_word} end_word={end_word} ini_quran={ini_quran} end_quran={end_quran}', file=args.outfile)

