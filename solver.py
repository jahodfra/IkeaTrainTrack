import argparse
import collections
import pickle
import string

import dynamic
import track


Material = collections.namedtuple('Material', 'straight turns ups, downs pillars')


def compute_all_paths(material):
    paths = dynamic.find_all_paths(material)
    print('number of paths:', len(paths))
    paths = set(map(track.normalize_path, paths))
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
    tracks = map(track.Track, paths)
    tracks = [t for t in tracks if t.is_valid(material)]
    set_of_tracks = set(tracks)
    can_be_simplified = lambda t: any(st in set_of_tracks for st in t.simplify())
    tracks = [t for t in tracks if not can_be_simplified(t)]
    print('number of unique paths:', len(tracks))
    for i, t in enumerate(tracks[:10], start=1):
        print(t.path)
        t.draw('preview%02d.png' % i)


if __name__ == '__main__':
    main()
