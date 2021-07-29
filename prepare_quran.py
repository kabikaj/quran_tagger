#!/usr/bin/env python3
#
#    prepare_quran.py
#
# prepare tanzil for quran_tagger
#
# output:
#   "qtext"   : [(1,1,1,1), (1,1,2,1), (1,1,2,2), ...]
#   "qblocks" : {"BSM": [0, 63, ...], "A" : [...], ...},
#   "qwords"  : {1: {1: {1: ("بِسْمِ", "بِسمِ"), 2: ("ٱللَّهِ", "اللَهِ"), ...}, ...}, ...}
#
# requirements:
#   * quran-uthmani.json
#
# usage:
#   $ cat quran-uthmani.json | python prepare_quran.py > quran.json
#
###################################################################

import sys
import ujson as json
from argparse import ArgumentParser, FileType

from quran_tagger import normalise, rasm

if __name__ == '__main__':

    parser = ArgumentParser(description='search quranic quotes in tafsir')
    parser.add_argument('infile', nargs='?', type=FileType('r'), default=sys.stdin, help='preprocessed tanzil quran')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=sys.stdout, help='prepared tanzil quran')
    args = parser.parse_args()

    tanzil = json.load(args.infile)

    qtext = []  # [qindex0, qindex1, ...]
    qblocs = {} # [rblocX: (qindA, qindB, indC, ...), rblocY: (...), ...]  // here qind are completed, i.e. s,v,w,b
    qwords = {} # {isura: {ivers: {iword: (word_ori, word_norm), ...}, ...}, ...}
    i = 0
    
    for sura in tanzil:
        isura = int(sura['sura'])
        for vers in sura['verses']:
            ivers = int(vers['verse'])
            for iword, word in enumerate(vers['full_text'].split(), 1):
                word_norm = normalise(word)
                blocks = rasm(word_norm).split()
                for ibloc, bloc in enumerate(blocks, 1):
                    qtext.append((isura, ivers, iword, ibloc))
                    qblocs[bloc] = qblocs.get(bloc, [])+[i]
                    i += 1
                if isura in qwords:
                    if ivers in qwords[isura]:
                        if iword not in qwords[isura][ivers]:
                            qwords[isura][ivers][iword] = (word, word_norm)
                    else:
                        qwords[isura][ivers] = {iword : (word, word_norm)}
                else:
                    qwords[isura] = {}
                    qwords[isura][ivers] = {iword : (word, word_norm)}

    json.dump({'qblocks': qblocs, 'qtext': qtext, 'qwords': qwords}, args.outfile)
