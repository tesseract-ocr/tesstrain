#!/usr/bin/env python3

import argparse
import io
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

# Get image size.
width, height = Image.open(args.image).size

# load gt
with io.open(args.txt, "r", encoding='utf-8') as f:
    lines = f.read().strip().split('\n')
    if len(lines) != 1:
        raise ValueError("ERROR: %s: Ground truth text file should contain exactly one line, not %s" % (args.txt, len(lines)))
    line = unicodedata.normalize('NFC', lines[0].strip())

if line:
    for i in range(1, len(line)):
        char = line[i]
        prev_char = line[i-1]
        if unicodedata.combining(char):
            print("%s 0 0 %d %d 0" % ((prev_char + char), width, height))
        elif not unicodedata.combining(prev_char):
            print("%s 0 0 %d %d 0" % (prev_char, width, height))
    if not unicodedata.combining(line[-1]):
        print("%s 0 0 %d %d 0" % (line[-1], width, height))
    print("\t 0 0 %d %d 0" % (width, height))
