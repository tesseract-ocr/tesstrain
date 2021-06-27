#!/usr/bin/env python3

# shuffle.py - shuffle lines in pseudo random order
#
# Usage:
#       shuffle.py [SEED [FILE]]
#
# Sort and shuffle the lines read from stdin in pseudo random order
# and write them to stdout.
#
# If FILE is given, then apply to that in-place (instead of stdin and stdout).
#
# The optional SEED argument is used as a seed for the random generator.
# A shuffled list can be reproduced by using the same seed again.

import random
import sys

# If at least one argument was given, the first argument is used as the seed.
if len(sys.argv) > 1:
    random.seed(sys.argv[1])

if len(sys.argv) > 2:
    fd0 = open(sys.argv[2], 'r')
else:
    fd0 = sys.stdin

# Read lines from standard input.
lines = fd0.readlines()

# First sort the input lines (directory entries may come in undefined order).
lines.sort()

# Then shuffle the lines.
random.shuffle(lines)

if len(sys.argv) > 2:
    fd1 = open(sys.argv[2], 'w')
else:
    fd1 = sys.stdout

# Write the shuffled lines to standard output.
fd1.writelines(lines)
