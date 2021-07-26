#!/usr/bin/env python3
#
#    quran_tagger_altafsir_test.py
#
# manual tester for quran tagger against altafsir data
#
# examples:
#   $ time cat tiny_example_altafsir.json | python quran_tagger_altafsir_test.py --debug --gold tiny_example_altafsir.gold &> tiny_example_altafsir.tagged
#   $ time cat altafsir-9-85-47-4-6.json | python quran_tagger_altafsir_test.py --gold altafsir-9-85-47-4-6.gold > altafsir-9-85-47-4-6.tagged
# 
#####################################################################################################################################################

import sys
import ujson as json
from argparse import ArgumentParser, FileType

from quran_tagger import tagger

if __name__ == '__main__':

    parser = ArgumentParser(description='manual test for quranic tagger')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='altafsir file')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='tagged text according to quran tagger')
    parser.add_argument('--gold', type=FileType('w'), help='tagged text according to gold standard')
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

    results = list(tagger(tok_text, debug=args.debug))

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
