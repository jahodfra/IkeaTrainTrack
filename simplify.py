#!/usr/local/bin/python3
"""
Eliminate tracks which can be contructed from already present tracks.

e.g. RRRRSRRRRS, RRRRRRRR -> RRRRRRRR
"""

import argparse
import sys

import track


DESCRIPTION = """\
Take tracks from standard input and print the ones which can be used to
construct the whole set.

Each track should be provided on a new line.

Algorithm for extension:
Extend round track in the opposite direction with S, RL, LR.
Prolong bridges. Replace uphill, downhill with straight segments.
"""


def can_be_simplified(t, set_of_tracks):
    return any(st in set_of_tracks for st in t.simplify())


def main():
    # TODO: algorithm expects that the shorten piece is also present in the set.
    # remove this condition.
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    args = parser.parse_args()
    tracks = set()
    for line in sys.stdin:
        path = line.strip()
        tracks.add(track.Track(path).normalize())
    tracks = [t for t in tracks if not can_be_simplified(t, tracks)]
    for t in tracks:
        print(t.path)


if __name__ == '__main__':
    main()
