#!/usr/bin/env python3

import argparse
import io
import unicodedata

from bidi import algorithm as uba
from PIL import Image

JOINERS = {'\u200c', '\u200d'}  # ZERO WIDTH NON-JOINER, ZERO WIDTH JOINER


def visual_order(text):
    """Return text in visual (left-to-right image) order for LSTM training.

    Unlike bidi.algorithm.get_display(), this
    * keeps ZWNJ/ZWJ: they have bidi class BN, which UBA rule X9 deletes, but
      they are meaningful in Persian, Urdu and Indic scripts;
    * does not mirror characters (rule L4): Tesseract labels a mirrored glyph
      with its logical code point, e.g. the stock fas/ara models read the
      right-hand bracket of an RTL "(...)" as U+0028.
    """
    storage = uba.get_empty_storage()
    storage['base_level'] = uba.get_base_level(text, False)
    storage['base_dir'] = ('L', 'R')[storage['base_level']]
    uba.get_embedding_levels(text, storage, False, False)
    chars = storage['chars']
    for i, ch in enumerate(chars):
        if ch['ch'] in JOINERS:
            # Take a neighbour's class so the joiner survives X9 without
            # changing how anything else is ordered.
            neighbour = chars[i - 1] if i else chars[i + 1] if i + 1 < len(chars) else None
            ch['type'] = ch['orig'] = neighbour['orig'] if neighbour else 'ON'
    uba.explicit_embed_and_overrides(storage, False)
    uba.resolve_weak_types(storage, False)
    uba.resolve_neutral_types(storage, False)
    uba.resolve_implicit_levels(storage, False)
    uba.reorder_resolved_levels(storage, False)
    return ''.join(ch['ch'] for ch in storage['chars'])

#
# command line arguments
#
arg_parser = argparse.ArgumentParser(
    """Creates tesseract WordStr box files for given (line) image text pairs"""
)

# Text ground truth
arg_parser.add_argument(
    '-t',
    '--txt',
    nargs='?',
    metavar='TXT',
    help='Line text (GT)',
    required=True,
)

# Image file
arg_parser.add_argument(
    '-i',
    '--image',
    nargs='?',
    metavar='IMAGE',
    help='Image file',
    required=True,
)

args = arg_parser.parse_args()

#
# main
#

# load image
with open(args.image, 'rb') as f:
    im = Image.open(f)
    width, height = im.size

# load gt
with io.open(args.txt, 'r', encoding='utf-8') as f:
    lines = f.read().strip().split('\n')
    if len(lines) != 1:
        raise ValueError(
            'ERROR: %s: Ground truth text file should contain exactly one line, not %s'
            % (args.txt, len(lines))
        )
    line = unicodedata.normalize('NFC', lines[0].strip())

# create WordStr line boxes for Indic & RTL
if line:
    line = visual_order(line)
    print('WordStr 0 0 %d %d 0 #%s' % (width, height, line))
    print('\t 0 0 %d %d 0' % (width, height))
