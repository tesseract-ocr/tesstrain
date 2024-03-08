#!/usr/bin/env python3

import unicodedata
import sys, getopt

def main(argv):
    txt_file = ''
    try:
        opts, args = getopt.getopt(argv,"h")
    except getopt.GetoptError:
        print('USAGE: count_chars.py <txt_file>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h','--help'):
            print('USAGE: count_chars.py <txt_file>')
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
            chars[char] +=1

    keys = list(chars.keys())
    keys.sort()
    print('Count\tCharacter\n-----\t---------')
    for char in keys:
        try:
            print(chars[char], '\t', char,
                  unicodedata.name(char))
        except:
            pass

if __name__ == "__main__":
   main(sys.argv[1:])
