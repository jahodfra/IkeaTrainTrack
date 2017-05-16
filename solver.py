import argparse
import collections
import itertools
import pickle
import string

from track import Track
from dynamic import find_all_paths


def shifts(track):
    for i in range(len(track)):
        yield track[i:] + track[:i] 


ROTATE_TRANSFORM = str.maketrans('RL', 'LR')
def normalize_track(track):
    # possible symmetries
    # translational - generate all translations and choose the biggest
    #                 lexicographycally
    # rotational    - change left rotation to right and choose the biggest
    #                 lexicographically
    # reverse path  - change the direction
    mirror_track = track.translate(ROTATE_TRANSFORM)
    reversed_track = track[::-1]
    reversed_mirror_track = mirror_track[::-1]
    return min(itertools.chain(
        shifts(track),
        shifts(mirror_track),
        shifts(reversed_track),
        shifts(reversed_mirror_track)
    ))


Material = collections.namedtuple('Material', 'straight turns ups, downs pillars')


def compute_all_paths(material):
    paths = find_all_paths(material)
    print('number of paths:', len(paths))
    paths = set(map(normalize_track, paths))
    print('number of unique paths:', len(paths))
    return paths


def main():
    parser = argparse.ArgumentParser(description='find all closed paths')
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

    filename = 'paths.pickle'
    try:
        paths = pickle.load(open(filename, 'rb'))
    except IOError:
        paths = compute_all_paths(material)
        pickle.dump(paths, open(filename, 'wb'))
    tracks = map(Track, paths)
    tracks = [t for t in tracks if t.is_valid(material)]
    print('number of unique paths:', len(tracks))
    for i, t in enumerate(tracks[:10], start=1):
        print(t.path)
        t.draw('preview%02d.png' % i)


if __name__ == '__main__':
    main()
