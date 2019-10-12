#!/usr/bin/env python3

import argparse
import io
import unicodedata
from PIL import Image

#
# command line arguments
#
arg_parser = argparse.ArgumentParser(description='Normalize all ground truth texts for the given text files.')
#arg_parser = argparse.ArgumentParser('''normalize.py''')

# Images.
arg_parser.add_argument("filename", help="filename of text file", nargs='*')

args = arg_parser.parse_args()

# Read all files and overwrite them with normalized text if necessary.
for filename in args.filename:
    with io.open(filename, "r", encoding="utf-8") as f:
        text = f.read()
        normalized_text = unicodedata.normalize('NFC', text)
        if text != normalized_text:
            print(filename)
            with io.open(filename, "w", encoding="utf-8") as out:
                out.write(normalized_text)
