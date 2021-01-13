#!/usr/bin/env python3

import argparse
import io
import unicodedata

# Command line arguments.
arg_parser = argparse.ArgumentParser(description='Normalize all ground truth texts for the given text files.')
arg_parser.add_argument("filename", help="filename of text file", nargs='*')
arg_parser.add_argument("-n", "--dry-run", help="show which files would be normalized but don't change them", action="store_true")
arg_parser.add_argument("-v", "--verbose", help="show ignored files", action="store_true")
arg_parser.add_argument("-f", "--form", help="normalization form (default: NFC)", choices=["NFC", "NFKC", "NFD", "NFKD"], default="NFC")

args = arg_parser.parse_args()

# Read all files and overwrite them with normalized text if necessary.
for filename in args.filename:
    with io.open(filename, "r", encoding="utf-8") as f:
        try:
            text = f.read()
        except UnicodeDecodeError:
            if args.verbose:
                print(filename + " (ignored)")
            continue
        normalized_text = unicodedata.normalize(args.form, text)
        if text != normalized_text:
            print(filename)
            if not args.dry_run:
                with io.open(filename, "w", encoding="utf-8") as out:
                    out.write(normalized_text)
