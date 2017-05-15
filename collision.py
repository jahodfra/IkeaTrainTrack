"""
Test if track collides with itself.
"""
import collections
import math


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


def path_intersections(track):
    # TODO: place positions of pillars
    segments = collections.defaultdict(list)
    for i, segment in enumerate(track.path):
        start = track.pos[i]
        end = track.pos[i+1]
        height = track.level[i]
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

