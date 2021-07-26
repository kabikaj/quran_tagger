# Quran tagger

Quran tagger identifies quranic quotes in any Arabic-scripted text.
The Quran tagger uses the tanzil Quran and it uses an archigraphemic representation of letterblocks for Arabic script. These two concepts have been develoed by Thomas Milo

## Usage

Examples of usage as script:
```bash
$ python quran_tagger.py --min 2 <(echo '["نرينك","بعض"]')
$ echo "نرينك بعض" | tr ' ' '\n' | grep . | jq -R -n -c '[inputs]' | python quran_tagger.py --min 2
```

In python code:
```python
from quran_tagger import tagger
for (ini_word, end_word), (ini_quran, end_quran) in tagger(["نرينك","بعض"], min_blocks=2):
    print(f'Found! ini_word={ini_word} end_word={end_word} ini_quran={ini_quran} end_quran={end_quran}')
```

## Author
Alicia Gonzalez Martinez, InterSaME project, Hamburg University

## Version
python 3.8