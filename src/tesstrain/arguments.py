# (C) Copyright 2014, Google Inc.
# (C) Copyright 2018, James R Barlow
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Argument handling utilities.
"""

import argparse
import atexit
import logging
import os
import pathlib
import platform
from datetime import date
from tempfile import TemporaryDirectory, mkdtemp

from tesstrain.generate import err_exit

log = logging.getLogger(__name__)


class TrainingArguments(argparse.Namespace):
    def __init__(self):
        super(TrainingArguments, self).__init__()
        self.uname = platform.uname().system.lower()
        self.lang_code = 'eng'
        self.timestamp = str(date.today())

        self._font_config_cache = TemporaryDirectory(prefix='font_tmp')
        self.font_config_cache = self._font_config_cache.name
        self.fonts_dir = (
            '/Library/Fonts/'
            if 'darwin' in self.uname
            else '/usr/share/fonts/'
        )

        self.max_pages = 0
        self.save_box_tiff = False
        self.overwrite = False
        self.linedata = False
        self.run_shape_clustering = False
        self.extract_font_properties = True
        self.distort_image = False

    def __eq__(self, other):
        return (
            argparse.Namespace.__eq__(self, other)
            and self.uname == other.uname
            and self.lang_code == other.lang_code
            and self.timestamp == other.timestamp
            and self.font_config_cache == other.font_config_cache
            and self.fonts_dir == other.fonts_dir
            and self.max_pages == other.max_pages
            and self.save_box_tiff == other.save_box_tiff
            and self.overwrite == other.overwrite
            and self.linedata == other.linedata
            and self.run_shape_clustering == other.run_shape_clustering
            and self.extract_font_properties == other.extract_font_properties
            and self.distort_image == other.distort_image
        )


def get_argument_parser():
    parser = argparse.ArgumentParser(
        prog='tesstrain',
        epilog="""
        The font names specified in --fontlist need to be recognizable by Pango using
        fontconfig. An easy way to list the canonical names of all fonts available on
        your system is to run text2image with --list_available_fonts and the
        appropriate --fonts_dir path.
        """,
    )
    parser.add_argument(
        '--fontlist',
        dest='fonts',
        nargs='+',
        type=str,
        help='A list of fontnames to train on.',
    )
    parser.add_argument(
        '--vertical_fontlist',
        dest='vertical_fonts',
        nargs='+',
        type=str,
        help='A list of fontnames to render vertical text.',
    )
    parser.add_argument('--fonts_dir', help='Path to font files.')
    parser.add_argument(
        '--tmp_dir', help='Path to temporary training directory.'
    )
    parser.add_argument(
        '--lang', metavar='LANG_CODE', dest='lang_code', help='ISO 639 code.'
    )
    parser.add_argument(
        '--langdata_dir',
        metavar='DATADIR',
        help='Path to tesseract/training/langdata directory.',
    )
    parser.add_argument('--maxpages', type=int, dest='max_pages')
    parser.add_argument(
        '--output_dir',
        metavar='OUTPUTDIR',
        help='Location of output traineddata file.',
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Safe to overwrite files in output_dir.',
    )
    parser.add_argument(
        '--save_box_tiff',
        action='store_true',
        help='Save box/tiff pairs along with lstmf files.',
    )
    parser.add_argument(
        '--linedata_only',
        dest='linedata',
        action='store_true',
        help='Only generate training data for lstmtraining.',
    )

    inputdata_group = parser.add_argument_group(
        'inputdata',
        'OPTIONAL flags for input data. If unspecified we will look for them in the langdata_dir directory.',
    )
    inputdata_group.add_argument(
        '--training_text',
        metavar='TEXTFILE',
        help='Text to render and use for training.',
    )
    inputdata_group.add_argument(
        '--wordlist',
        dest='wordlist_file',
        metavar='WORDFILE',
        help='Word list for the language ordered by decreasing frequency.',
    )

    parser.add_argument('--extract_font_properties', action='store_true')
    parser.add_argument(
        '--noextract_font_properties',
        dest='extract_font_properties',
        action='store_false',
    )

    parser.add_argument(
        '--distort_image', dest='distort_image', action='store_true'
    )

    tessdata_group = parser.add_argument_group(
        'tessdata',
        (
            'OPTIONAL flag to specify location of existing traineddata files, required during feature extraction. '
            'If unspecified will use TESSDATA_PREFIX defined in the current environment.'
        ),
    )
    tessdata_group.add_argument(
        '--tessdata_dir',
        metavar='TESSDATADIR',
        help='Path to tesseract/tessdata directory.',
    )

    parser.add_argument(
        '--exposures',
        metavar='EXPOSURES',
        action='append',
        nargs='+',
        help='A list of exposure levels to use (e.g. -1,0,1).',
    )

    parser.add_argument(
        '--ptsize',
        metavar='PT_SIZE',
        type=int,
        default=12,
        help='Size of printed text.',
    )

    return parser


def verify_parameters_and_handle_defaults(ctx):
    log.debug(ctx)

    if not ctx.lang_code:
        err_exit('Need to specify a language --lang')
    if not ctx.langdata_dir:
        err_exit('Need to specify path to language files --langdata_dir')
    if not ctx.tessdata_dir:
        tessdata_prefix = os.environ.get('TESSDATA_PREFIX', '')
        if not tessdata_prefix:
            err_exit(
                'Need to specify a --tessdata_dir or have a '
                'TESSDATA_PREFIX variable defined in your environment'
            )
        else:
            ctx.tessdata_dir = tessdata_prefix
    if not ctx.output_dir:
        ctx.output_dir = mkdtemp(
            prefix=f'trained-{ctx.lang_code}-{ctx.timestamp}'
        )
        log.info(f'Output directory set to: {ctx.output_dir}')

    # Location where intermediate files will be created.
    if not ctx.tmp_dir:
        ctx.training_dir = mkdtemp(prefix=f'{ctx.lang_code}-{ctx.timestamp}')
    else:
        ctx.training_dir = mkdtemp(
            prefix=f'{ctx.lang_code}-{ctx.timestamp}', dir=ctx.tmp_dir
        )
    # Location of log file for the whole run.
    ctx.log_file = pathlib.Path(ctx.training_dir) / 'tesstrain.log'
    log.info(f'Log file location: {ctx.log_file}')

    def show_tmpdir_location(training_dir):
        # On successful exit we will delete this first; on failure we want to let the user
        # know where the log is
        if pathlib.Path(training_dir).exists():
            print(f'Temporary files retained at: {training_dir}')

    atexit.register(show_tmpdir_location, ctx.training_dir)

    # Take training text and wordlist from the langdata directory if not
    # specified in the command-line.
    if not ctx.training_text:
        ctx.training_text = (
            pathlib.Path(ctx.langdata_dir)
            / ctx.lang_code
            / f'{ctx.lang_code}.training_text'
        )
    if not ctx.wordlist_file:
        ctx.wordlist_file = (
            pathlib.Path(ctx.langdata_dir)
            / ctx.lang_code
            / f'{ctx.lang_code}.wordlist'
        )

    ctx.word_bigrams_file = (
        pathlib.Path(ctx.langdata_dir)
        / ctx.lang_code
        / f'{ctx.lang_code}.word.bigrams'
    )
    ctx.numbers_file = (
        pathlib.Path(ctx.langdata_dir)
        / ctx.lang_code
        / f'{ctx.lang_code}.numbers'
    )
    ctx.punc_file = (
        pathlib.Path(ctx.langdata_dir)
        / ctx.lang_code
        / f'{ctx.lang_code}.punc'
    )
    ctx.bigram_freqs_file = pathlib.Path(ctx.training_text).with_suffix(
        '.training_text.bigram_freqs'
    )
    ctx.unigram_freqs_file = pathlib.Path(ctx.training_text).with_suffix(
        '.training_text.unigram_freqs'
    )
    ctx.train_ngrams_file = pathlib.Path(ctx.training_text).with_suffix(
        '.training_text.train_ngrams'
    )
    ctx.generate_dawgs = 1

    log.debug(ctx)
    return ctx
