# distutils: language=c++
#### distutils: sources=search.cpp
import time
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector
from cython.operator cimport dereference

cdef extern from "state.hpp":
    cdef cppclass State:
        State()
        State(int ax, int bx, int ay, int by, int angle, int level, int straight, int turns, int ups, int downs, int pillars)
        int ax, bx, ay, by, angle, level, straight, turns, ups, downs, pillars


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
    ( 1,  0,  0, -1),
    ( 0,  1, -1,  0),
    ( 0, -1, -1,  0),
    (-1,  0,  0, -1),
    (-1,  0,  0,  1),
    ( 0, -1,  1,  0),
    ( 0,  1,  1,  0),
    ( 1,  0,  0,  1),
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
        STR_SHIFT[angle] + ( 0,  0, -1,  0,  0,  0),
        STR_SHIFT[angle] + ( 0,  1,  0,  0, -1,  0),
        STR_SHIFT[angle] + ( 0, -1,  0,  0,  0, -1),
        R_SHIFT[angle]   + ( 1,  0,  0, -1,  0,  0),
        R_SHIFT[angle-1] + (-1,  0,  0, -1,  0,  0),
    ]


def forward_search(m):
    cdef unordered_set[State] visited
    py_visited = set()
    _forward_search(&visited, m.straight, m.turns, m.ups, m.downs, m.pillars)
    for s in visited:
        py_visited.add((s.ax, s.bx, s.ay, s.by, s.angle, s.level, s.straight, s.turns, s.ups, s.downs, s.pillars))
    return py_visited

cdef void _forward_search(unordered_set[State]* visited, int mstraight, int mturns, int mups, int mdowns, int mpillars):
    cdef int levela, levelb, level, pillars, segment
    cdef int angle, straight, turns, ups, downs
    cdef int ax, bx, ay, by, bi
    cdef State ns
    cdef vector[State] border, new_border;
    cdef int[400] neighbours_map
    # 8 * 5 * 10
    for angle in range(8):
        for segment, vect in enumerate(_neighbours(angle)):
            for i, n in enumerate(vect):
                neighbours_map[angle*50+segment*10+i] = n
    # 7,7,7,7,3,3,5,5,5,5,5 = 28+6+25 = 59bit < 64bit
    # We can encode whole configuration into one uint64
    # ax, bx, ay, by, angle, level, ...
    # Because sqrt(2) is irational number we have to track numbers in
    # the following base.
    # ax, ay is position in the grid in multiples of sqrt(2)/2 ~ 0.71
    # bx, by is position in the grid in multiples of 1-sqrt(2)/2 ~ 0.29

    border.push_back(State(0, 0, 0, 0, 0, 0, mstraight, mturns, mups, mdowns, mpillars))
    for _ in range(mstraight + mturns + mups + mdowns):
        new_border.clear()
        for a in border:
            for segment in range(5):
                angle = a.angle
                bi = angle*50 + segment*10
                levela = PILLARS[2*segment]
                levelb = PILLARS[2*segment + 1]
                level = a.level
                pillars = a.pillars
                ax = a.ax
                bx = a.bx
                ay = a.ay
                by = a.by
                straight = a.straight
                turns = a.turns
                ups = a.ups
                downs = a.downs
                pillars += levela * level + levelb
                ax += neighbours_map[bi+0]
                bx += neighbours_map[bi+1]
                ay += neighbours_map[bi+2]
                by += neighbours_map[bi+3]
                angle = (angle + neighbours_map[bi+4]) % 8
                level += neighbours_map[bi+5]
                straight += neighbours_map[bi+6]
                turns += neighbours_map[bi+7]
                ups += neighbours_map[bi+8]
                downs += neighbours_map[bi+9]
                if turns < angle < 8 - turns:
                    # It's not possible to turn back
                    # with the current number of turns.
                    continue
                if not (0 <= level <= downs):
                    continue
                if straight < 0 or turns < 0 or ups < 0 or downs < 0 or pillars < 0:
                    continue
                if max(abs(ax), abs(bx), abs(ay), abs(by)) > abs(straight + turns + ups + downs):
                    # It's not possible to return back
                    # with the current number of segments.
                    continue
                ns = State(
                    ax, bx, ay, by, angle, level,
                    straight, turns, ups, downs, pillars)
                if visited.find(ns) == visited.end():
                    new_border.push_back(ns)
                    visited.insert(ns)
        border = new_border


cdef backward_search(unordered_set[State]* visited, material):
    cdef int levela, levelb, level, pillars, segment, bi, angle
    cdef int ax, bx, ay, by, straight, turns, ups, downs
    cdef int mstraight, mturns, mups, mdowns, mpillars
    cdef int[400] neighbours_map
    cdef unsigned int j;
    cdef State ps, s
    cdef vector[State] states, new_states;
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
    for s in dereference(visited):
        if (s.ax == 0 and s.bx == 0 and s.ay == 0 and s.by == 0 and s.angle == 0
            and s.level == 0):
            paths.append('')
            states.push_back(s)
    while paths:
        new_paths = []
        new_states.clear()
        for j in range(states.size()):
            a = states[j]
            for segment in range(5):
                angle = a.angle
                bi = angle*50 + segment*10
                levela = PILLARS[2*segment]
                levelb = PILLARS[2*segment + 1]
                ax = a.ax
                bx = a.bx
                ay = a.ay
                by = a.by
                level = a.level
                straight = a.straight
                turns = a.turns
                ups = a.ups
                downs = a.downs
                pillars = a.pillars
                level -= neighbours_map[bi+5]
                # pillars have to be counted from the previous level
                pillars -= levela * level + levelb
                ax -= neighbours_map[bi+0]
                bx -= neighbours_map[bi+1]
                ay -= neighbours_map[bi+2]
                by -= neighbours_map[bi+3]
                angle = (angle - neighbours_map[bi+4]) % 8
                straight -= neighbours_map[bi+6]
                turns -= neighbours_map[bi+7]
                ups -= neighbours_map[bi+8]
                downs -= neighbours_map[bi+9]
                if (ax == 0 and bx == 0 and ay == 0 and by == 0 and angle == 0
                   and level == 0 and straight == mstraight and turns == mturns
                   and downs == mdowns and pillars == mpillars):
                    final.append(paths[j] + segment_names[segment])
                    continue
                ps = State(
                    ax, bx, ay, by,
                    angle,
                    level,
                    straight, turns, ups, downs,
                    pillars
                )
                if visited.find(ps) != visited.end():
                    new_paths.append(paths[j] + segment_names[segment])
                    new_states.push_back(ps)
        paths = new_paths
        states = new_states
    return final


def find_all_paths(m):
    t = time.clock()
    cdef unordered_set[State] visited
    _forward_search(&visited, m.straight, m.turns, m.ups, m.downs, m.pillars)
    print('frw took {:.2f}s'.format(time.clock() - t))
    t = time.clock()
    paths = backward_search(&visited, m)
    print('back took {:.2f}s'.format(time.clock() - t))
    return paths

