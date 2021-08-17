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
#   $ echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ مِنكُمْ وَٱلصَّابِرِينَ وَنَبْلُوَ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python -m cProfile quran_tagger.py --min 3
#
# examples:
#   $ echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ مِنكُمْ وَٱلصَّابِرِينَ وَنَبْلُوَ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py
#   $ python quran_tagger.py --min 2 <(echo '["نرينك","بعض"]')
#   $ echo "نرينك بعض" | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 2
#
#   $ echo وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ ٱلْمُجَاهِدِينَ ب وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ وَلَنَبْلُوَنَّكُمْ حَتَّىٰ نَعْلَمَ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 2
#   $ echo فقال تعالى: إِلاَّ أَن تَكُونَ تِجَٰرَةً عَن تَرَاضٍ مِّنْكُمْ فلا بأس | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 3
#
#   $ echo يَجْحَدُونَ بِآيَاتِ ٱللَّهِ وَحَاقَ بِه مَّا كَانُواْ بِهِ يَسْتَهْزِئُونَ | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 3 --debug # error in input (7-55-21-78-79), it is with mim وَحَاقَ بِهم
# 
################################################################################################################################################################

import os
import re
import sys
import ujson as json
from argparse import ArgumentParser, FileType

from util import normalise, rasm


RED='\033[1;31m' #DEBUG
RESET='\033[0m' #DEBUG

MIN_TOKENS = 4
SAFE_LENGTH = 5
RELATED_WINDOW = 80

_MY_PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_MY_PATH, 'quran_simple.json')) as quranfp:
    QURAN = json.load(quranfp)

#with open(os.path.join(_MY_PATH, 'stopwords.json')) as fp:
#    STOPWORDS = set([rasm(normalise(w)) for w in json.load(fp)])
with open(os.path.join(_MY_PATH, 'stopwords2.json')) as fp:
    STOPWORDS = set(json.load(fp))


QURAN['qrasm'] = {k : set(d) for k, d in QURAN['qrasm'].items()}


class TokensError(Exception):
    """ Raised when the number of tokens is illogical.

    """
    pass

def tagger(words, qstruct=QURAN, min_tokens=MIN_TOKENS, safe_length=SAFE_LENGTH, rasm_match=False, debug=False):
    """ tag words with quranic quotations.

    Args:
        words (list): text as a list of words.
        qstruct (dict): quran structure.
        min_tokens (int): minimum number of non-stopword words to accept as a match.
        safe_length (int): minimum number of words to accept as a match regardless their nature.
        rasm (bool): accept pure rasm matches.
        debug (bool): show debugging info.

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
        TokensError: if number of blocks is smaller than 1.

    """
    if min_tokens <= 0:
        raise TokensError('The minimum number of words must be at least 1')

    words_rasm = [(ori, norm, rasm(norm)) for ori, norm in ((w, normalise(w)) for w in words)]
    end_of_chains = dict() # { end_offset : { chain_length : [(start_offset, quran_start_offset), ...], ... }
    nwords = len(words_rasm)

    for i, (ori_tok, norm_tok, rasm_tok) in enumerate(words_rasm):

        # stop searching when the remaining tokens are smaller than min_tokens
        if i > nwords - min_tokens:
            break

        for iquran in qstruct['qrasm'].get(rasm_tok, set()):

            if rasm_tok in STOPWORDS:   #FIXME stopwords
                chain_rasm = set()      #FIXME stopwords
            else:                       #FIXME stopwords
                chain_rasm = {rasm_tok} #FIXME stopwords

            chain_norm_text = [norm_tok]                        #FIXME last filtering
            chain_norm_quran = [qstruct['qtext'][iquran][1][1]] #FIXME last filtering

            j = 0
            while i+j < nwords-1:
                j += 1
                next_word_rasm = words_rasm[i+j][2]
                if not next_word_rasm in qstruct['qrasm'] or not iquran+j in qstruct['qrasm'][next_word_rasm]:
                    break

                if next_word_rasm not in STOPWORDS:  #FIXME stopwords
                    chain_rasm.add(next_word_rasm)   #FIXME stopwords
                
                chain_norm_text.append(words_rasm[i+j][1])                #FIXME last filtering
                chain_norm_quran.append(qstruct['qtext'][iquran+j][1][1]) #FIXME last filtering
            else:
                j+=1
            
            if len(chain_rasm) >= min_tokens or j >= safe_length: #FIXME stopwords
                
                if rasm_match or ' '.join(chain_norm_text) == ' '.join(chain_norm_quran):  #FIXME last filtering

                    j -= 1
                    if not i+j in end_of_chains:
                        end_of_chains[i+j] = {j+1: [(i, iquran)]}
                    elif not j+1 in end_of_chains[i+j]:
                        end_of_chains[i+j][j+1] = [(i, iquran)]
                    else:
                        end_of_chains[i+j][j+1].append((i, iquran))

    
    # keep only the longest token chain(s) for each endpoint:
    filtered_longest = dict()
    for end_i in end_of_chains.keys():
        m = max(end_of_chains[end_i].keys())
        filtered_longest[end_i] = end_of_chains[end_i][m]

    # filter out overlapping chains:
    if filtered_longest:
        filtered_longest = sorted(filtered_longest.items(), key=lambda x: x[1])
        filtered_overlap = [filtered_longest[0]]
        for end, group in filtered_longest[1:]:
            ini = group[0][0]
            prev_end = filtered_overlap[-1][0]
            prev_ini = filtered_overlap[-1][1][0][0]
            # there is overlap
            if not prev_end < ini:
                prev_size = prev_end - prev_ini
                curr_size = end - ini
                if curr_size > prev_size:
                    filtered_overlap.pop()
                elif curr_size < prev_size:
                    continue
                else:
                    qini = group[0][1]
                    prev_qini = filtered_overlap[-1][1][0][1]
                    #FIXME what to do if overlapping parts have same length? Currently nothing is done...
                    print(f'WARNING! overlap Quran quotations with same length: {ini}(q{qini})-{end} vs '
                          f'{prev_ini}(q{prev_qini})-{prev_end}', file=sys.stderr) #TRACE
                    #FIXME
                    #if len(filtered_overlap)>1:
                    #    prev_prev_qini = filtered_overlap[-2][1][0][1]
                    #    print(f'>>>prev_prev_qini={prev_prev_qini}', file=sys.stderr)
                    #    if (prev_qini - RELATED_WINDOW) < prev_prev_qini:
                    #        print('A. es menor!!')
                    #    elif (qini - RELATED_WINDOW) < prev_prev_qini:
                    #        print('B. es menor!!')
                    #    else:
                    #        print('FUCK!!')
            filtered_overlap.append((end, group))
    else:
        filtered_overlap = []

    for text_end, starts in filtered_overlap:        
        text_ini = starts[0][0]

        if debug:
            text_norm = ' '.join((x[1] for x in words_rasm[text_ini:text_end+1]))
            text_ori = ' '.join((x[0] for x in words_rasm[text_ini:text_end+1]))
            print(f'{RED}@DEBUG@ ini={text_ini}  end={text_end}', file=sys.stderr) #TRACE
            print(f'        ori =  "{text_ori}"  norm =  "{text_norm}"', file=sys.stderr) #TRACE

        quran_ids = []
        for _, quran_ini in starts:

            quran_end = quran_ini + (text_end - text_ini)

            qindex_ini = qstruct['qtext'][quran_ini][0]
            qindex_end = qstruct['qtext'][quran_end][0]

            if debug:
                quran_ori = ' '.join(w[0] for _, w in qstruct['qtext'][quran_ini:quran_end+1])
                quran_norm = ' '.join(w[1] for _, w in qstruct['qtext'][quran_ini:quran_end+1])
                print(f'@DEBUG@ qini={quran_ini}({qindex_ini})  qend={quran_end}({qindex_end})', file=sys.stderr) #TRACE
                print(f'        qori = "{quran_ori}"  qnorm = "{quran_norm}"{RESET}', file=sys.stderr) #TRACE
        
            quran_ids.append((qindex_ini, qindex_end, quran_ini, quran_end))
        
        yield (text_ini, text_end), quran_ids


if __name__ == '__main__':

    parser = ArgumentParser(description='tag text with Quranic quotations')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='tokenised words to tag in json format')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='quranic indexes found')
    parser.add_argument('--min', type=int, default=MIN_TOKENS, help=f'minimum number of referential words to accept as a match [DEFAULT = {MIN_TOKENS}]')
    parser.add_argument('--safe', type=int, default=SAFE_LENGTH, help=f'minimum number of words to accept as a match regardless their nature [DEFAULT = {SAFE_LENGTH}]')
    parser.add_argument('--rasm', action='store_true', help='accept pure rasm matches')
    parser.add_argument('--debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    words = json.load(args.infile)

    for (word_ini, word_end), quranids in tagger(words, min_tokens=args.min, safe_length=args.safe, rasm_match=args.rasm, debug=args.debug):
        print(f'Found! word_ini={word_ini} word_end={word_end}', file=args.outfile)
        for qindex_ini, qindex_end, quran_ini, quran_end in quranids:
            print(f'  quran_ini={qindex_ini}({quran_ini}) quran_end={qindex_end}({quran_end})', file=args.outfile)

