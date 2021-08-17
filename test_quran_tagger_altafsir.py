#!/usr/bin/env python3
#
#    test_quran_tagger_altafsir.py
#
# manual tester for quran tagger against altafsir data
#
# get altfsir files for testing:
#   $ for f in $(find ~/Desktop/development_230320/corpus/sources/altafsir/data/all/final -type f -name "*.json" | sort -R | tail -4) ;
#     do cp $f altafsir_in ; done
#
# examples:
#   $ cat data/altafsir_in/tiny_example_altafsir.json |
#     python test_quran_tagger_altafsir.py --min 3 --debug --gold data/altafsir_out/tiny_example_altafsir.gold.xml &> data/altafsir_out/tiny_example_altafsir.tagged.xml
#   $ cat data/altafsir_in/altafsir-9-85-47-4-6.json |
#     python test_quran_tagger_altafsir.py --min 3 --debug --gold data/altafsir_out/altafsir-9-85-47-4-6.gold.xml &> data/altafsir_out/altafsir-9-85-47-4-6.tagged.xml
#   
#   example with same length overlap:
#   $ cat data/altafsir_in_500/altafsir-1-4-106-4-4.json | python test_quran_tagger_altafsir.py --min 3 --gold altafsir-1-4-106-4-4.gold.xml > altafsir-1-4-106-4-4.tagged.xml
# 
##############################################################################################################################################################################

import re
import sys
import ujson as json
from argparse import ArgumentParser, FileType

from quran_tagger import tagger, MIN_TOKENS

REGEX_COMPLETE_TAGS = re.compile(r'\{(.+?)\}')

if __name__ == '__main__':

    parser = ArgumentParser(description='manual test for quranic tagger')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='altafsir file')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='tagged text according to quran tagger')
    parser.add_argument('--gold', type=FileType('w'), help='tagged text according to gold standard')
    parser.add_argument('--min', type=int, default=MIN_TOKENS, help='minimum number of words accepted as a match')
    parser.add_argument('--rasm', action='store_true', help='accept pure rasm matches')
    parser.add_argument('--quiet', action='store_true', help='do not indicate as attributes the quran indexes matched in the xml tag')
    parser.add_argument('--debug', action='store_true', help='show debugging info')
    args = parser.parse_args()

    doc = json.load(args.infile)

    text = doc['text']
    text = text[1:] #FIXME bug: the initial space should not be there
    for ann in doc['annotation']['aya'][::-1]:
        text = text[:ann['end']] + "\n</quran>\n" + text[ann['end']:]
        text = text[:ann['start']] + "\n<quran>\n" + text[ann['start']:]

    text = REGEX_COMPLETE_TAGS.sub(r'\n<quran>\n\1\n</quran>\n', text)

    # text with annotations from altafsir
    print(text, file=args.gold)

    tok_text = [w for w in doc['text'].split()]

    results = list(tagger(tok_text, min_tokens=args.min, rasm_match=args.rasm, debug=args.debug))

    results_proc = [(tinds, '; '.join(f'ini={":".join(map(str,qiini))} end={":".join(map(str,qiend))}' for qiini, qiend, *_ in qinds))
        for tinds, qinds in results]

    if args.debug:
        print('\n====== results ======', file=args.outfile) #TRACE
        for res in results_proc:
            print(res, file=args.outfile) #TRACE

    opening_tags = {ini:attrib for (ini, _), attrib in results_proc}
    closing_tags = {end for (_, end), _ in results_proc}

    if args.debug:
        print('\n====== tagged tok_text ======', file=args.outfile) #TRACE

    for i, tok in enumerate(tok_text):
        if i in opening_tags:
            print(f'\n<quran{"" if args.quiet else " "+opening_tags[i]}>\n{tok} ', end='', file=args.outfile)
        elif i in closing_tags:
            print(f'{tok}\n</quran>\n', end='', file=args.outfile)
        else:
            print(tok, end=' ', file=args.outfile)


