#!/usr/bin/env python3
#
#    evaluate_altafsir.py
#
# check accuracy of tagger against selected corpus from altafsir
#
# get altfsir files for testing:
#   $ for f in $(find ~/Desktop/development_230320/corpus/sources/altafsir/data/all/final -type f -name "*.json" | sort -R | tail -2000) ;
#     do cp $f data/altafsir_in ; done
#
# execute tagger:
#   $ time for f in $(find data/altafsir_in -type f) ; do cat $f | python test_quran_tagger_altafsir.py --quiet
#     --gold "data/altafsir_out/$(basename $f .json).gold.xml" > "data/altafsir_out/$(basename $f .json).tagged.xml" ; done
#
# execute evaluator:
#   $ python evaluate_altafsir.py data/altafsir_out
#
#########################################################################################################################################

import os
import re
import sys
from bs4 import BeautifulSoup
from argparse import ArgumentParser, FileType


RM_NUM_REGEX = re.compile(r'\([0-9]+\)')

if __name__ == '__main__':

    parser = ArgumentParser(description='check accuracy of tagger against selected corpus from altafsir')
    parser.add_argument('dir', help='directory containing results of tagger and gold standard')
    parser.add_argument('--min', type=int, required=False, help='minimum number of words in match to compare')
    args = parser.parse_args()

    correct, not_found, false_positive = 0, 0, 0

    aux, aux2 = {}, {} #FIXME files with high amount of failures
    for fp in set(os.path.splitext(fo.path)[0].rsplit('.', 1)[0] for fo in os.scandir(args.dir)):
        
        with open(f'{fp}.gold.xml') as goldfp, open(f'{fp}.tagged.xml') as taggfp:

            fn = os.path.basename(fp)

            #if fn != 'altafsir-9-84-56-13-26': #DEBUG
            #    continue #DEBUG

            # check if all the quran marked in altafsir is included in the tagged text

            gold_quotes = set(RM_NUM_REGEX.sub('', tag.text.strip()) for tag in BeautifulSoup(goldfp.read(), 'lxml').find_all('quran'))
            tagg_quotes = set(RM_NUM_REGEX.sub('', tag.text.strip()) for tag in BeautifulSoup(taggfp.read(), 'lxml').find_all('quran'))

            if args.min:
                gold_quotes = set(s for s in gold_quotes if len(s.split())>=args.min)
                tagg_quotes = set(s for s in tagg_quotes if len(s.split())>=args.min)

            # precision
            for text in gold_quotes:
                if text in tagg_quotes:
                    correct += 1
                else:
                    not_found += 1
                    if len(text.split())>5: #FIXME
                        aux[fn] = aux.get(fn, 0)+1 #FIXME files with high amount of failures

            #recall
            for text in tagg_quotes:
                if text not in gold_quotes:
                    false_positive += 1
                    if len(text.split())>6: #FIXME
                        aux2[fn] = aux2.get(fn, 0)+1 #FIXME files with high amount of failures

    print(f'correct        = {correct}')
    print(f'not found      = {not_found}')
    print(f'false positive = {false_positive}')


    #FIXME -------------------files with high amount of failures ------------------------------------------
    #high_not_found = max(aux.values())
    #for fn in aux:
    #    if aux[fn] == high_not_found:
    #        print(f'** {fn}  not_found={high_not_found}')
    #high_false_pos = max(aux2.values())
    #for fn in aux2:
    #    if aux2[fn] == high_false_pos:
    #        print(f'** {fn}  false_positives={high_false_pos}')
    #for fn, cnt in sorted(aux2.items(), key=lambda x: x[1], reverse=True):
    #    print(cnt, fn)
    #for fn, cnt in sorted(aux.items(), key=lambda x: x[1], reverse=True):
    #    print(cnt, fn)
