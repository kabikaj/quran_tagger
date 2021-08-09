#!/usr/bin/env python3
#
#    evaluate_altafsir.py
#
# check accuracy of tagger against selected corpus from altafsir
#
# get altfsir files for testing:
#   $ for f in $(find ~/Desktop/development_230320/corpus/sources/altafsir/data/all/final -type f -name "*.json" | sort -R | tail -2000) ;
#     do cp $f altafsir_in ; done
#
# execute tagger:
#   $ time for f in $(find altafsir_in -type f) ; do cat $f | python test_quran_tagger_altafsir.py --quiet
#     --gold "altafsir_out/$(basename $f .json).gold.xml" > "altafsir_out/$(basename $f .json).tagged.xml" ; done
#
# execute evaluaror:
#   $ python evaluate_altafsir.py altafsir_out
#
#########################################################################################################################################

import os
import sys
from bs4 import BeautifulSoup
from argparse import ArgumentParser, FileType


if __name__ == '__main__':

    parser = ArgumentParser(description='check accuracy of tagger against selected corpus from altafsir')
    parser.add_argument('dir', help='directory containing results of tagger and gold standard')
    args = parser.parse_args()

    correct, not_found, false_positive = 0, 0, 0

    for fp in set(os.path.splitext(fo.path)[0].rsplit('.', 1)[0] for fo in os.scandir(args.dir)):
        
        with open(f'{fp}.gold.xml') as goldfp, open(f'{fp}.tagged.xml') as taggfp:

            fn = os.path.basename(fp)

            #if fn != 'altafsir-9-84-56-13-26': #DEBUG
            #    continue #DEBUG

            # check if all the quran marked in altafsir is included in the tagged text

            gold_quotes = set(tag.text.strip() for tag in BeautifulSoup(goldfp.read(), 'lxml').find_all('quran'))
            tagg_quotes = set(tag.text.strip() for tag in BeautifulSoup(taggfp.read(), 'lxml').find_all('quran'))

            # precision
            for text in gold_quotes:
                if text in tagg_quotes:
                    correct += 1
                else:
                    not_found += 1

            #recall
            for text in tagg_quotes:
                if text not in gold_quotes:
                    false_positive += 1  


    print(f'correct        = {correct}')
    print(f'not found      = {not_found}')
    print(f'false positive = {false_positive}')
