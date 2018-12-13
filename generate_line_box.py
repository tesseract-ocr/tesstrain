#!/usr/bin/env python

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

# load image
with open(args.image, "rb") as f:
    width, height = Image.open(f).size

# load gt
with io.open(args.txt, "r", encoding='utf-8') as f:
    lines = f.read().strip().split('\n')

for line in lines:
    if line.strip():
        for i in range(1, len(line)):
            char = line[i]
            prev_char = line[i-1]
            if unicodedata.combining(char):
                print(u"%s %d %d %d %d 0" % ((prev_char + char), 0, 0, width, height))
            elif not unicodedata.combining(prev_char):
                print(u"%s %d %d %d %d 0" % (prev_char, 0, 0, width, height))
        if not unicodedata.combining(line[-1]):
            print(u"%s %d %d %d %d 0" % (line[-1], 0, 0, width, height))
        print(u"%s %d %d %d %d 0" % ("\t", width, height, width+1, height+1))
