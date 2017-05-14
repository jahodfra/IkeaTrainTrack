# bridges
# there has to be the same number of uphills as downhills
# length of up hills is limited every up hill after up hill needs
# 2 support pillars same for downhill

# for elevated track every piece needs 1 pillar ending piece needs two.
# that brings number of elevated tracks to maximaly 1x3 or 2x1

import argparse
import collections
import itertools
import math
import pickle
import string

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


def get_height(path):
    # Reconstruct height
    level = []
    cl = 0
    
    for s in path:
        level.append(cl)
        if s == 'U':
            cl += 1
        elif s == 'D':
            cl -= 1
    else:
        level.insert(0, cl)
    # minimal level should be 0
    ml = min(level)
    level = [cl - ml for cl in level]
    return level


STRAIGHT_SIZE = 1.0
TURN_SIZE = 2.0 - math.sqrt(2.0)


def get_pos(path):
    x = y = .0
    angle = 0
    pos = []
    for s in path:
        if s == 'R':
            angle += 1
            r = TURN_SIZE
        elif s == 'L':
            angle -= 1
            r = TURN_SIZE
        else:
            r = STRAIGHT_SIZE
        pos.append((x, y))
        a = angle * math.pi / 4.0
        x += math.cos(a) * r
        y += -math.sin(a) * r
    pos.append((x, y))
    return pos, angle


def count_pillars(path, level):
    lp = len(path)
    pillars = 0
    # up after a segment
    #   2 times level
    #   1 times level if the following segment is not down and there is no
    #   pass below (that's quite a hack so we do not consider that)
    # up after a down
    #   2 times level
    #   1 times level if the following segment is not down (same hack)
    # down after a segment
    #   2 times level - 1
    # down after an up (that's less than estimated)
    #   level - 1

    for i in range(lp):
        if path[i] == 'U':
            pillars += 2 * level[i]
        elif path[i] == 'D':
            pillars += level[i] - 1
            if path[(i-1) % lp] != 'U':
                # we can move one of support pillar backward
                # to support both segments
                pillars += level[i] - 1
        else:
            pillars += level[i]
    return pillars


def test_conflict(s1, l1, start1, end1, s2, l2, start2, end2):
    return False


LineSegment = collections.namedtuple('LineSegment', 'id start end')


def point_on_line(start, end, coef):
    sx, sy = start
    ex, ey = end
    c2 = 1.0 - coef
    return (ex*coef + sx*c2, ey*coef + sy*c2)


def minus(v1, v2):
    return v1[0]-v2[0], v1[1]-v2[1]


def cross(v1, v2):
    return v1[0]*v2[1] - v1[1]*v2[0]


def almost_zero(n):
    return math.fabs(n) <= 1e-3


def line_intersection(line1, line2):
    a = minus(line1.end, line1.start)
    b = minus(line2.end, line2.start)
    cd = minus(line2.start, line1.start)
    cab = cross(a, b)
    if almost_zero(cab):
        # coincident lines
        return almost_zero(cd[0]) and almost_zero(cd[1])
    # solution according to the cramer's rule
    t = cross(a, cd) / cab
    s = cross(cd, b) / cab
    return (0 <= s <= 1.0) and (0 <= t <= 1.0)


def path_intersections(path, level, pos):
    # TODO: place positions of pillars
    lp = len(path)
    segments = collections.defaultdict(list)
    for i, segment in enumerate(path):
        start = pos[i]
        end = pos[(i+1)%lp]
        height = level[i]
        if segment == 'U':
            line = LineSegment(i, start, point_on_line(start, end, 0.8))
            segments[height].append(line)
            line = LineSegment(i, point_on_line(start, end, 0.2), end)
            segments[height+1].append(line)
        elif segment == 'D':
            line = LineSegment(i, start, point_on_line(start, end, 0.8))
            segments[height].append(line)
            line = LineSegment(i, point_on_line(start, end, 0.2), end)
            segments[height-1].append(line)
        else:
            line = LineSegment(i, start, end)
            segments[height].append(line)

    for lines in segments.values():
        events = []
        for line in lines:
            start = line.start
            end = line.end
            if start[0] > end[0]:
                start, end = end, start
            events.append((start[0], 0, line))
            events.append((end[0], 1, line))
        events.sort()
        opened = set()
        for pos, etype, line in events:
            if etype == 0:
                for line2 in opened:
                    if abs(line2.id - line.id) > 1 and line_intersection(line, line2):
                        return True
                opened.add(line)
            else:
                opened.remove(line)
    return False

def validate_path(path, material):
    """Ensure that the paths do not intersect
    Also enforce more stricter condition on pillars.
    """
    if not path:
        return False
    if path.count('U') != path.count('D'):
        # unbalanced
        return False

    level = get_height(path)
    pos, angle = get_pos(path)

    if angle % 8 != 0:
        # does not return to original direction
        return False

    endx, endy = pos[-1]
    if not almost_zero(endx) or not almost_zero(endy):
        # does not return to original point
        return False

    # count pillars and remove paths with lot of pillars
    if material.pillars < count_pillars(path, level):
        return False

    if path_intersections(path, level, pos):
        return False

    return True


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
    paths = [p for p in paths if validate_path(p, material)]
    print('number of unique paths:', len(paths))
    for path in paths[:10]:
        print(path)


if __name__ == '__main__':
    main()
