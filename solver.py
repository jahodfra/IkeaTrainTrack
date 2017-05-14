# bridges
# there has to be the same number of uphills as downhills
# length of up hills is limited every up hill after up hill needs
# 2 support pillars same for downhill

# for elevated track every piece needs 1 pillar ending piece needs two.
# that brings number of elevated tracks to maximaly 1x3 or 2x1

import argparse
import collections
import copy
import itertools
import math
import pickle
import string
import time


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

STR_SHIFT = (
    (1, 1, 0, 0),
    (1, 0, -1, 0),
    (0, 0, -1, -1),
    (-1, 0, -1, 0),
    (-1, -1, 0, 0),
    (-1, 0, 1, 0),
    (0, 0, 1, 1),
    (1, 0, 1, 0),
)

R_SHIFT = (
    (1, 0, 0, -1),
    (0, 1, -1, 0),
    (0, -1, -1, 0),
    (-1, 0, 0, -1),
    (-1, 0, 0, 1),
    (0, -1, 1, 0),
    (0, 1, 1, 0),
    (1, 0, 0, 1),
)

# Represents Segment: (a, b) where change in pillars is a*level+b
PILLARS = {
    'S': (-1, 0),
    'U': (-2, 0),
    'D': (-1, 1),
    'R': (-1, 0),
    'L': (-1, 0),
}

def _neighbours(angle):
    return {
        'S': STR_SHIFT[angle] + (0, 0, -1, 0, 0, 0),
        'U': STR_SHIFT[angle] + (0, 1, 0, 0, -1, 0),
        'D': STR_SHIFT[angle] + (0, -1, 0, 0, 0, -1),
        'R': R_SHIFT[angle]   + (1, 0, 0, -1, 0, 0),
        'L': R_SHIFT[angle-1] + (-1, 0, 0, -1, 0, 0),
    }

def get_neighbours_map():
    neighbours_map = {}
    for angle in range(8):
        neighbours_map[angle] = _neighbours(angle)
    return neighbours_map

from dynamic import dynamic_programming
    
    
def back_propagation(visited, material):
    neighbours_map = get_neighbours_map()
    # turn right, turn left has to be changed differently
    backward_map = copy.deepcopy(neighbours_map)
    for angle in range(8):
        backward_map[angle]['R'] = neighbours_map[(angle-1)%8]['R']
        backward_map[angle]['L'] = neighbours_map[(angle+1)%8]['L']

    end_state = (0, 0, 0, 0, 0, 0, material.straight, material.turns, material.ups, material.downs, material.pillars)
    paths = []
    final = []
    for s in visited:
        if s[:6] == (0, 0, 0, 0, 0, 0):
            paths.append(('', s))
    while paths:
        new_paths = []
        for path, a in paths:
            #for segment, ps in get_neighbours(a):
            for segment, b in backward_map[a[4]].items():
                levela, levelb = PILLARS[segment]
                level = a[5] - b[5]
                # pillars have to be counted from the previous level
                pillars = a[10] - (levela * level + levelb)
                ps = (a[0]-b[0], a[1]-b[1], a[2]-b[2], a[3]-b[3], (a[4]-b[4])%8, level, a[6]-b[6], a[7]-b[7], a[8]-b[8], a[9]-b[9], pillars)
                if ps == end_state:
                    final.append(segment + path)
                elif ps in visited:
                    new_paths.append((segment + path, ps))
        paths = new_paths
    return final


def compute_all_paths(material):
    t = time.clock()
    visited = dynamic_programming(material)
    print('frw took {:.2f}s'.format(time.clock() - t))
    t = time.clock()
    paths = back_propagation(visited, material)
    print('back took {:.2f}s'.format(time.clock() - t))
    print('number of paths:', len(paths))
    paths = set(map(normalize_track, paths))
    print('number of unique paths:', len(paths))
    return paths


def test_conflict(s1, l1, start1, end1, s2, l2, start2, end2):
    return False


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
TURN_SIZE = 2.0 * math.sin(math.pi / 8.0)


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
    if math.fabs(endx) > 1e-10 or math.fabs(endy) > 1.e-10:
        # does not return to original point
        return False

    # count pillars and remove paths with lot of pillars
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
    if material.pillars < pillars:
        return False

    for i in range(lp):
        for j in range(i):
            if test_conflict(
                path[i], level[i], pos[i], pos[(i+1) % lp],
                path[j], level[j], pos[j], pos[j+1],
            ):
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


if __name__ == '__main__':
    main()