#!/usr/local/bin/python3

import argparse
import collections

import dynamic
import track


Material = collections.namedtuple(
    'Material', 'straight turns ups, downs pillars')


def can_be_simplified(t, set_of_tracks):
    return any(st in set_of_tracks for st in t.simplify())


def normalize_paths(paths):
    filtered = []
    paths = set(paths)
    while paths:
        path = paths.pop()
        min_path = path
        for symetric_path in track.all_symetries(path):
            paths.discard(symetric_path)
            if symetric_path < min_path:
                min_path = symetric_path
        filtered.append(min_path)
    return filtered


def compute_tracks(material):
    paths = dynamic.find_all_paths(material)
    paths = normalize_paths(paths)
    tracks = [track.Track(p) for p in paths]
    tracks = [t for t in tracks if t.is_valid(material)]
    set_of_tracks = set(tracks)
    tracks = [t for t in tracks if not can_be_simplified(t, set_of_tracks)]
    return tracks


DESCRIPTION = """\
Write out all enclosed path with given set of elements.
Each path is written on a new line.
Elements: S - straight segment, U - uphill segment, D - downhill segment,
R - turn right, L - turn left\
"""


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        '--turns',
        dest='turns', type=int, default=12, help='number of turn segments')
    parser.add_argument(
        '--straight',
        dest='straight', type=int, default=4,
        help='number of straight segments')
    parser.add_argument(
        '--ups',
        dest='ups', type=int, default=2, help='number of uphill segments')
    parser.add_argument(
        '--downs',
        dest='downs', type=int, default=2, help='number of downhill segments')
    parser.add_argument(
        '--pillars',
        dest='pillars', type=int, default=4, help='number of pillars')
    args = parser.parse_args()
    material = Material(
        turns=args.turns,
        straight=args.straight,
        ups=args.ups,
        downs=args.downs,
        pillars=args.pillars)

    tracks = compute_tracks(material)
    for t in tracks:
        print(t.path)


if __name__ == '__main__':
    main()
