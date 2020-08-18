#!/usr/bin/env python3

import argparse
import io
import unicodedata

import bidi.algorithm
from PIL import Image

#
# command line arguments
#
arg_parser = argparse.ArgumentParser('''Creates tesseract WordStr box files for given (line) image text pairs''')

# Text ground truth
arg_parser.add_argument('-t', '--txt', nargs='?', metavar='TXT', help='Line text (GT)', required=True)

# Image file
arg_parser.add_argument('-i', '--image', nargs='?', metavar='IMAGE', help='Image file', required=True)

args = arg_parser.parse_args()

#
# main
#

# load image
with open(args.image, "rb") as f:
    im = Image.open(f)
    width, height = im.size

# load gt
with io.open(args.txt, "r", encoding='utf-8') as f:
    lines = f.read().strip().split('\n')
    if len(lines) != 1:
        raise ValueError("ERROR: %s: Ground truth text file should contain exactly one line, not %s" % (args.txt, len(lines)))
    line = unicodedata.normalize('NFC', lines[0].strip())

# create WordStr line boxes for Indic & RTL
if line:
    line = bidi.algorithm.get_display(line)
    print("WordStr 0 0 %d %d 0 #%s" % (width, height, line))
    print("\t 0 0 %d %d 0" % (width, height))
