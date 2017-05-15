"""
Provides Track class
"""

import math

import collision


STRAIGHT_SIZE = 1.0
TURN_SIZE = 2.0 - math.sqrt(2.0)


class Track:
    def __init__(self, path):
        self.path = path
        self._angles = None
        self._pos = None
        self._level = None

    @property
    def level(self):
        # Reconstruct height
        if self._level is None:
            level = []
            cl = 0
            
            for s in self.path:
                level.append(cl)
                if s == 'U':
                    cl += 1
                elif s == 'D':
                    cl -= 1
            else:
                level.insert(0, cl)
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
            self._angles.append(angle)
            if s == 'R':
                angle += 1
                r = TURN_SIZE
            elif s == 'L':
                angle -= 1
                r = TURN_SIZE
            else:
                r = STRAIGHT_SIZE
            self._pos.append((x, y))
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

