#!/usr/bin/env python3

import io
import argparse
import unicodedata
from PIL import Image, ImageChops, ImageOps

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

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

# load image
with open(args.image, "rb") as f:
    cropped = trim(Image.open(f))
    img_with_border = ImageOps.expand(cropped,border=10,fill='white')
    width, height = img_with_border.size
    img_with_border.save(args.image)

# load gt
with io.open(args.txt, "r", encoding='utf-8') as f:
    lines = f.read().strip().split('\n')

# create WordStr line boxes for Indic & RTL
for line in lines:
    if line.strip():
        print(u"%s %d %d %d %d 0 #%s" % ("WordStr", 0, 0, width, height, line))
        print(u"%s %d %d %d %d 0" % ("\t", width, height, width+1, height+1))
