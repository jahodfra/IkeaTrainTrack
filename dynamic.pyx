import time


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
cdef int[10] PILLARS = [
    -1, 0,
    -2, 0,
    -1, 1,
    -1, 0,
    -1, 0,
]


def _neighbours(angle):
    return [
        STR_SHIFT[angle] + (0, 0, -1, 0, 0, 0),
        STR_SHIFT[angle] + (0, 1, 0, 0, -1, 0),
        STR_SHIFT[angle] + (0, -1, 0, 0, 0, -1),
        R_SHIFT[angle]   + (1, 0, 0, -1, 0, 0),
        R_SHIFT[angle-1] + (-1, 0, 0, -1, 0, 0),
    ]


def dynamic_programming(material):
    cdef int levela, levelb, level, pillars, segment
    cdef int angle, straight, turns, ups, downs
    cdef int ax, bx, ay, by, bi
    cdef int[400] neighbours_map
    # 8 * 5 * 10
    for angle in range(8):
        for segment, vect in enumerate(_neighbours(angle)):
            for i, n in enumerate(vect):
                neighbours_map[angle*50+segment*10+i] = n
    border = set()
    #border.add(State(pos=Pos(0, 0, 0, 0), angle=0, level=0, material=material))
    # 7,7,7,7,3,3,5,5,5,5,5 = 28+6+25 = 59bit < 64bit
    # We can encode whole configuration into one uint64
    # ax, bx, ay, by, angle, level, ...
    # Because sqrt(2) is irational number we have to track numbers in
    # the following base.
    # ax, ay is position in the grid in multiples of sqrt(2)/2 ~ 0.71
    # bx, by is position in the grid in multiples of 1-sqrt(2)/2 ~ 0.29

    border.add((0, 0, 0, 0, 0, 0, material.straight, material.turns, material.ups, material.downs, material.pillars))
    visited = set()
    for _ in range(sum([material.straight, material.turns, material.ups, material.downs])):
        new_border = set()
        for a in border:
            # alpha(pos(pillars(x))
            # pillars(pos-1(alpha-1(y)))
            angle = a[4]
            for segment in range(5):
                bi = angle*50 + segment*10
                levela = PILLARS[2*segment]
                levelb = PILLARS[2*segment + 1]
                level = a[5]
                pillars = a[10] + levela * level + levelb
                ax = a[0] + neighbours_map[bi+0]
                bx = a[1] + neighbours_map[bi+1]
                ay = a[2] + neighbours_map[bi+2]
                by = a[3] + neighbours_map[bi+3]
                angle = (angle + neighbours_map[bi+4]) % 8
                level += neighbours_map[bi+5]
                straight = a[6] + neighbours_map[bi+6]
                turns = a[7] + neighbours_map[bi+7]
                ups = a[8] + neighbours_map[bi+8]
                downs = a[9] + neighbours_map[bi+9]
                if turns < angle < 7 - turns:
                    # It's not possible to turn back
                    # with the current number of turns.
                    continue
                if pillars < level or downs < level or level < 0:
                    continue
                if straight < 0 or turns < 0 or ups < 0 or downs < 0 or pillars < 0:
                    continue
                if max(abs(ax), abs(bx), abs(ay), abs(by)) > straight + turns + ups + downs:
                    # It's not possible to return back
                    # with the current number of segments.
                    continue
                new_border.add((ax, bx, ay, by, angle, level, straight, turns, ups, downs, pillars))
        visited.update(new_border)
        border = new_border
    return visited


def back_propagation(visited, material):
    cdef int levela, levelb, level, pillars, segment, bi, angle
    cdef int ax, bx, ay, by, straight, turns, ups, downs
    cdef int mstraight, mturns, mups, mdowns, mpillars
    cdef int[400] neighbours_map
    forward = {}
    for angle in range(8):
        forward[angle] = _neighbours(angle)
    # turn right, turn left has to be changed differently
    for angle in range(8):
        backward = forward[angle][:3] + [
            forward[(angle-1)%8][3], forward[(angle+1)%8][4]]
        for segment, vect in enumerate(backward):
            for i, n in enumerate(vect):
                neighbours_map[angle*50+segment*10+i] = n

    mstraight = material.straight
    mturns = material.turns
    mups = material.ups
    mdowns = material.downs
    mpillars = material.pillars
    paths = []
    final = []
    segment_names = 'SUDRL'
    for s in visited:
        if (s[0] == 0 and s[1] == 0 and s[2] == 0 and s[3] == 0 and s[4] == 0
            and s[5] == 0):
            paths.append(('', s))
    while paths:
        new_paths = []
        for path, a in paths:
            for segment in range(5):
                angle = a[4]
                bi = angle*50 + segment*10
                levela = PILLARS[2*segment]
                levelb = PILLARS[2*segment + 1]
                level = a[5] - neighbours_map[bi+5]
                # pillars have to be counted from the previous level
                pillars = a[10] - (levela * level + levelb)
                ax = a[0]-neighbours_map[bi+0]
                bx = a[1]-neighbours_map[bi+1]
                ay = a[2]-neighbours_map[bi+2]
                by = a[3]-neighbours_map[bi+3]
                angle = (angle - neighbours_map[bi+4]) % 8
                straight = a[6]-neighbours_map[bi+6]
                turns = a[7]-neighbours_map[bi+7]
                ups = a[8]-neighbours_map[bi+8]
                downs = a[9]-neighbours_map[bi+9]
                ps = (
                    ax, bx, ay, by,
                    angle,
                    level,
                    straight, turns, ups, downs,
                    pillars
                )
                if (ax == 0 and bx == 0 and ay == 0 and by == 0 and angle == 0
                   and level == 0 and straight == mstraight and turns == mturns
                   and downs == mdowns and pillars == mpillars):
                    final.append(path + segment_names[segment])
                elif ps in visited:
                    new_paths.append((path + segment_names[segment], ps))
        paths = new_paths
    return final


def find_all_paths(material):
    t = time.clock()
    visited = dynamic_programming(material)
    print('frw took {:.2f}s'.format(time.clock() - t))
    t = time.clock()
    paths = back_propagation(visited, material)
    print('back took {:.2f}s'.format(time.clock() - t))
    return paths

