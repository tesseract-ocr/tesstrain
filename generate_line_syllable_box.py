#!/usr/bin/env python3

import io
import argparse
import unicodedata
from PIL import Image

#
# command line arguments
#
arg_parser = argparse.ArgumentParser('''Creates tesseract box files for given (line) image text pairs''')

# Text ground truth
arg_parser.add_argument('-t', '--txt', nargs='?', metavar='TXT', help='Line text (GT)', required=True)

# Image file
arg_parser.add_argument('-i', '--image', nargs='?', metavar='IMAGE', help='Image file', required=True)

args = arg_parser.parse_args()

#
# main
#

# https://stackoverflow.com/questions/6805311/combining-devanagari-characters
# Letters are category Lo (Letter, Other), vowel signs are category Mc (Mark, Spacing Combining), 
# virama is category Mn (Mark, Nonspacing) and spaces are category Zs (Separator, Space).

def splitclusters(s):
    """Generate the grapheme clusters for the string s. (Not the full
    Unicode text segmentation algorithm, but probably good enough for
    Devanagari.)

    """
# http://pyright.blogspot.com/2009/12/pythons-unicodedata-module.html
# The combining code is typically zero.  The virama gets its own special code of nine.
# i.e. unicodedata.category=Mn unicodedata.combining=9 
# (Could be used to extend for other Indic languages).

    virama = u'\N{DEVANAGARI SIGN VIRAMA}'
    cluster = u''
    last = None
    for c in s:
        cat = unicodedata.category(c)[0]
        if cat == 'M' or cat == 'L' and last == virama:
            cluster += c
        else:
            if cluster:
                yield cluster
            cluster = c
        last = c
    if cluster:
        yield cluster

# load image
with open(args.image, "rb") as f:
    width, height = Image.open(f).size

# load gt
with io.open(args.txt, "r", encoding='utf-8') as f:
    lines = f.read().strip().split('\n')

for line in lines:
    if line.strip():
        for syllable in (splitclusters(line)):
            print(u"%s %d %d %d %d 0" % (syllable, 0, 0, width, height))
            print(u"%s %d %d %d %d 0" % ("\t", width, height, width+1, height+1))
