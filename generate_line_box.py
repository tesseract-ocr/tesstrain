#!/usr/bin/python

import argparse
import re
import unicodedata
from PIL import Image

#
# command line arguments
#
arg_parser = argparse.ArgumentParser('''Creates tesseract box files for given (line) image text pairs''')

# clipping XML file
arg_parser.add_argument('-t', '--txt', type=argparse.FileType('r'), nargs='?', metavar='TXT', help='Line text (GT)', required=True)

# Image file
arg_parser.add_argument('-i', '--image', nargs='?', metavar='IMAGE', help='Image file', required=True)

args = arg_parser.parse_args()

#
# main
#

# load image
im = Image.open(file(args.image, "r"))
image = re.sub("\\.[^\\.]+$", "", re.sub("^[^/]+/", "", args.image))
width, height = im.size

for line in args.txt:
    line = line.strip().decode("utf-8")
    for i in range(1, len(line)):
        char = line[i]
        prev_char = line[i-1]
        if unicodedata.combining(char):
            print("%s %d %d %d %d 0" % ((prev_char + char).encode("utf-8"), 0, 0, width, height))
        elif not unicodedata.combining(prev_char):
            print("%s %d %d %d %d 0" % (prev_char.encode("utf-8"), 0, 0, width, height))
    if not unicodedata.combining(line[-1]):
        print("%s %d %d %d %d 0" % (line[-1].encode("utf-8"), 0, 0, width, height))
    print("%s %d %d %d %d 0" % ("\t", width, height, width+1, height+1))
