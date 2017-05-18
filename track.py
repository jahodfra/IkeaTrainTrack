"""
Provides Track class
"""

import collections
import math
import itertools
from PIL import Image, ImageDraw, ImageFont

import collision


STRAIGHT_SIZE = 1.0
TURN_SIZE = math.sqrt(2.0 - math.sqrt(2.0))


def shifts(path):
    for i in range(len(path)):
        yield path[i:] + path[:i]


ROTATE_TRANSFORM = str.maketrans('RL', 'LR')
def normalize_path(path):
    # possible symmetries
    # translational - generate all translations and choose the biggest
    #                 lexicographycally
    # rotational    - change left rotation to right and choose the biggest
    #                 lexicographically
    # reverse path  - change the direction
    mirror_path = path.translate(ROTATE_TRANSFORM)
    reversed_path = path[::-1]
    reversed_mirror_path = mirror_path[::-1]
    return min(itertools.chain(
        shifts(path),
        shifts(mirror_path),
        shifts(reversed_path),
        shifts(reversed_mirror_path)
    ))


class Track:
    def __init__(self, path):
        self.path = path
        self._angles = None
        self._pos = None
        self._level = None

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, o):
        return self.path == o.path

    def __ne__(self, o):
        return not self == o

    def normalize(self):
        return Track(normalize_path(self.path))

    def _simplify(self):
        path = self.path
        lp = len(path)
        def find_segment(match):
            lm = len(match)
            for i in range(lp):
               if path[i:min(i+lm, lp)] + path[:max(i+lm-lp, 0)]  == match:
                   yield i

        def replace_segment(path, i, lm, replace):
            return path[max(i+lm-lp, 0):i] + replace + path[i+lm:]

        def replace_pair(match, replace):
            lm = len(match)
            for i in find_segment(match):
                yield replace_segment(path, i, lm, replace)

        def remove_pair(pair1, pair2):
            occ1 = [[] for _ in range(8)]
            occ2 = [[] for _ in range(8)]
            for i in find_segment(pair1):
                occ1[self.angle[i]].append(i)
            for i in find_segment(pair2):
                occ2[self.angle[i]].append(2)
            for angle in range(8):
                for a in occ1[angle]:
                    for b in occ2[angle]:
                        if a == b:
                            continue
                        elif a > b:
                            a, b = b, a
                        p = replace_segment(path, a, len(pair1), '')
                        yield replace_segment(p, b - len(pair1), len(pair2), '')

        # shorten bridges
        yield from replace_pair('US', 'SU')
        yield from replace_pair('SD', 'DS')

        # shorten track
        yield from remove_pair('S', 'S')
        yield from remove_pair('RL', 'LR')
        yield from remove_pair('SS', 'UD')
        yield from remove_pair('UD', 'UD')

    def simplify(self):
        for p in self._simplify():
            yield Track(p).normalize()

    @property
    def level(self):
        # Reconstruct height
        if self._level is None:
            level = [0]
            cl = 0

            for s in self.path:
                if s == 'U':
                    cl += 1
                elif s == 'D':
                    cl -= 1
                level.append(cl)
            # minimal level should be 0
            ml = min(level)
            self._level = [cl - ml for cl in level]
        return self._level

    @property
    def pos(self):
        if self._pos is None:
            self._count_pos()
        return self._pos

    @property
    def angle(self):
        if self._angles is None:
            self._count_pos()
        return self._angles

    def _count_pos(self):
        x = y = .0
        angle = 0
        self._angles = []
        self._pos = []
        for s in self.path:
            self._pos.append((x, y))
            self._angles.append(angle % 8)
            if s == 'R':
                a = (angle + 0.5) * math.pi / 4.0
                angle += 1
                r = TURN_SIZE
            elif s == 'L':
                a = (angle - 0.5) * math.pi / 4.0
                angle -= 1
                r = TURN_SIZE
            else:
                r = STRAIGHT_SIZE
                a = angle * math.pi / 4.0
            x += math.cos(a) * r
            y += -math.sin(a) * r
        self._pos.append((x, y))
        self._angles.append(angle)

    def count_pillars(self):
        level = self.level
        path = self.path
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

    def is_valid(self, material):
        """Ensure that the paths do not intersect
        Also enforce more stricter condition on pillars.
        """
        path = self.path
        if not path:
            return False
        if path.count('U') != path.count('D'):
            # unbalanced
            return False

        if self.angle[-1] % 8 != 0:
            # does not return to original direction
            return False

        endx, endy = self.pos[-1]
        if not collision.almost_zero(endx) or not collision.almost_zero(endy):
            # does not return to original point
            return False

        # count pillars and remove paths with lot of pillars
        if material.pillars < self.count_pillars():
            return False

        if collision.path_intersections(self):
            return False

        return True

    def draw(self, filename):
        BORDER = 50
        GRID_SIZE = 50
        FONT_SIZE = 20
        TICK_SIZE = 3
        COLORS = ['#aaaaaa', '#aa11aa', '#aa1111']

        # Mirror coordinates by x axis.
        pos = [(x, -y) for x, y in self.pos]
        minx = min(x for x, y in pos)
        maxx = max(x for x, y in pos)
        miny = min(y for x, y in pos)
        maxy = max(y for x, y in pos)
        w = round((maxx - minx) * GRID_SIZE + 2 * BORDER)
        h = round((maxy - miny) * GRID_SIZE + 2 * BORDER)

        def transform(point):
            x, y = point
            x = round(GRID_SIZE*(x - minx) + BORDER)
            y = round(GRID_SIZE*(y - miny) + BORDER)
            return x, y

        # Create new image filled with black color.
        image = Image.new('RGB', (w, h))
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(font='data/NunitoSans-Regular.ttf', size=FONT_SIZE)
        draw.text((10, 10), self.path, font=font, fill=(255, 255, 255))
        sx, sy = transform((.0, .0))
        draw.arc((sx-5, sy-5, sx+5, sy+5), 0, 360, '#FF3333')
        for i, s in enumerate(self.path):
            # TODO: draw turns by arc
            a = self.angle[i] * math.pi / 4.0
            if s == 'R':
                r = TURN_SIZE
            elif s == 'L':
                r = TURN_SIZE
            else:
                r = STRAIGHT_SIZE
            level = self.level[i]
            if s == 'D':
                level -= 1
            r = round(r * GRID_SIZE)
            color = COLORS[level]
            if s == 'U':
                x, y = transform(pos[i])
                x2 = round(x + math.cos(a - .1) * r)
                y2 = round(y + math.sin(a - .1) * r)
                x3 = round(x + math.cos(a + .1) * r)
                y3 = round(y + math.sin(a + .1) * r)
                draw.line((x, y, x2, y2), fill=color)
                draw.line((x, y, x3, y3), fill=color)
                draw.line((x2, y2, x3, y3), fill=color)
            elif s == 'D':
                x, y = transform(pos[i+1])
                x2 = round(x - math.cos(a - .1) * r)
                y2 = round(y - math.sin(a - .1) * r)
                x3 = round(x - math.cos(a + .1) * r)
                y3 = round(y - math.sin(a + .1) * r)
                draw.line((x, y, x2, y2), fill=color)
                draw.line((x, y, x3, y3), fill=color)
                draw.line((x2, y2, x3, y3), fill=color)
            elif s == 'L':
                x, y = transform(pos[i])
                sa = (self.angle[i] / 4.0 + 0.5) * math.pi
                r = GRID_SIZE
                sx = round(x - math.cos(sa) * r)
                sy = round(y - math.sin(sa) * r)
                d = self.angle[i] * 45 + 45
                draw.arc((sx-r, sy-r, sx+r, sy+r), d, d + 45, fill=color)
            elif s == 'R':
                x, y = transform(pos[i])
                sa = (self.angle[i] / 4.0 + 1.5) * math.pi
                r = GRID_SIZE
                sx = round(x - math.cos(sa) * r)
                sy = round(y - math.sin(sa) * r)
                d = self.angle[i] * 45 - 90
                draw.arc((sx-r, sy-r, sx+r, sy+r), d, d + 45, fill=color)
            else:
                assert s == 'S'
                x, y = transform(pos[i])
                x2 = round(x + math.cos(a) * r)
                y2 = round(y + math.sin(a) * r)
                draw.line((x, y, x2, y2),
                    fill=color)
            x, y = transform(pos[i])
            x1 = round(x - math.cos(a + math.pi / 2.) * TICK_SIZE)
            y1 = round(y - math.sin(a + math.pi / 2.) * TICK_SIZE)
            x2 = round(x + math.cos(a + math.pi / 2.) * TICK_SIZE)
            y2 = round(y + math.sin(a + math.pi / 2.) * TICK_SIZE)
            draw.line((x1, y1, x2, y2), fill=color)

        image.save(filename)
