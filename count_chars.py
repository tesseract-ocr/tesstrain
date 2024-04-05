#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2024 Christine Roughan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import getopt
import sys
import unicodedata


def main(argv):
    txt_file = ''
    try:
        opts, args = getopt.getopt(argv, 'h')
    except getopt.GetoptError:
        print('USAGE: count_chars.py <txt_file>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(
                'USAGE: count_chars.py <txt_file> | sort -n -r > <txt_file>.charcount'
            )
            sys.exit()
    for arg in args:
        txt_file = arg

    inFile = open(txt_file)
    rawText = inFile.read()
    inFile.close()

    chars = {}
    for char in rawText:
        if char not in chars:
            chars[char] = 1
        else:
            chars[char] += 1

    keys = list(chars.keys())
    keys.sort()
    for char in keys:
        try:
            print(chars[char], '\t', char, '\t', unicodedata.name(char))
        except:
            pass


if __name__ == '__main__':
    main(sys.argv[1:])
