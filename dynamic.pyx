def material_pieces(m):
    return m.straight + m.turns + m.ups + m.downs

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

def get_neighbours_map():
    neighbours_map = {}
    for angle in range(8):
        neighbours_map[angle] = _neighbours(angle)
    return neighbours_map

def dynamic_programming(material):
    cdef int levela, levelb, level, pillars, segment
    cdef int angle, straight, turns, ups, downs
    cdef int ax, bx, ay, by
    neighbours_map = get_neighbours_map()
    border = set()
    #border.add(State(pos=Pos(0, 0, 0, 0), angle=0, level=0, material=material))
    # 7,7,7,7,3,3,5,5,5,5,5 = 28+6+25 = 59bit < 64bit
    # We can encode whole configuration into one uint64
    # ax, bx, ay, by, angle, level, ...
    border.add((0, 0, 0, 0, 0, 0, material.straight, material.turns, material.ups, material.downs, material.pillars))
    visited = set()
    for _ in range(material_pieces(material)):
        new_border = set()
        for a in border:
            # alpha(pos(pillars(x))
            # pillars(pos-1(alpha-1(y)))
            angle = a[4]
            na = neighbours_map[angle]
            for segment in range(5):
                b = na[segment]
                levela = PILLARS[2*segment]
                levelb = PILLARS[2*segment + 1]
                level = a[5]
                pillars = a[10] + levela * level + levelb
                level += b[5]
                ax = a[0] + b[0]
                bx = a[1] + b[1]
                ay = a[2] + b[2]
                by = a[3] + b[3]
                angle = (angle + b[4]) % 8
                straight = a[6] + b[6]
                turns = a[7] + b[7]
                ups = a[8] + b[8]
                downs = a[9] + b[9]
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
