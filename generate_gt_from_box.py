#!/usr/bin/env python3

import argparse
import io

#
# command line arguments
#
arg_parser = argparse.ArgumentParser(
    '''Creates groundtruth files from text2image generated box files''')

# Text ground truth
arg_parser.add_argument('-t', '--txt', nargs='?',
                        metavar='TXT', help='Line text (GT)', required=True)

# Text box file
arg_parser.add_argument('-b', '--box', nargs='?', metavar='BOX',
                        help='text2image generated box file (BOX)', required=True)

args = arg_parser.parse_args()

#
# main
# uses "λ" for substitution to  get the space delimiters - change for Greek text which uses "λ"
#

gtstring = io.StringIO()
gtfile = open(args.txt, "w", encoding='utf-8')
with io.open(args.box, "r", encoding='utf-8') as boxfile:
    print(''.join(line.replace("  ", "λ ").split(' ', 1)[0] for line in boxfile if line), file=gtstring)
gt = gtstring.getvalue().replace("λ", " ").replace("\t", "\n")
print(gt, file=gtfile)
