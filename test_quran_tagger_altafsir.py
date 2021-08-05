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
#   $ time cat altafsir_in/tiny_example_altafsir.json |
#     python test_quran_tagger_altafsir.py --min 3 --debug --gold altafsir_out/tiny_example_altafsir.gold.xml &> altafsir_out/tiny_example_altafsir.tagged.xml
#   $ time cat altafsir_in/altafsir-9-85-47-4-6.json |
#     python test_quran_tagger_altafsir.py --min 3 --debug --gold altafsir_out/altafsir-9-85-47-4-6.gold.xml &> altafsir_out/altafsir-9-85-47-4-6.tagged.xml
# 
#####################################################################################################################################################

import sys
import ujson as json
from argparse import ArgumentParser, FileType

from quran_tagger import tagger, MIN_TOKENS

if __name__ == '__main__':

    parser = ArgumentParser(description='manual test for quranic tagger')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='altafsir file')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='tagged text according to quran tagger')
    parser.add_argument('--gold', type=FileType('w'), help='tagged text according to gold standard')
    parser.add_argument('--min', type=int, default=MIN_TOKENS, help='minimum number of blocks to accept as a match (at least 2)')
    parser.add_argument('--rasm', action='store_true', help='accept pure rasm matches')
    parser.add_argument('--debug', action='store_true', help='show debugging info')
    args = parser.parse_args()

    doc = json.load(args.infile)

    text = doc['text']
    for ann in doc['annotation']['aya'][::-1]:
        text = text[:ann['end']] + "\n</quran>\n" + text[ann['end']:]
        text = text[:ann['start']] + "\n<quran>\n" + text[ann['start']:]

    # text with annotations from altafsir
    print(text, file=args.gold)

    tok_text = [w for w in doc['text'].split()]

    results = list(tagger(tok_text, min_tokens=args.min, rasm_match=args.rasm, debug=args.debug))

    if args.debug:
        print('\n====== results ======', file=args.outfile) #TRACE
        for res in results: print(res, file=args.outfile) #TRACE

    out = []
    for i, tok in enumerate(tok_text):
        found = False
        for (ini, end), (qini, qend) in results:
            sura_ini, vers_ini, word_ini = qini
            sura_end, vers_end, word_end = qend
            if i == ini:
                out.append(f'\n<quran ini="{sura_ini},{vers_ini},{word_ini}" end="{sura_end},{vers_end},{word_end}">\n'+tok)
                found = True
                break
            if i == end:
                out.append(f'\n</quran>\n'+tok)
                found = True
                break
        if not found:
            out.append(tok)

    if args.debug:
        print('\n====== tagged tok_text ======', file=args.outfile) #TRACE

    # text with annotations from quran tagger
    print(' '.join(out), file=args.outfile)
