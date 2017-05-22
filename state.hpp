/** One point in the state space **/
#include <stdlib.h>
#include <functional>

struct State {
    int ax, bx, ay, by, angle, level;
    int straight, turns, ups, downs, pillars;
    int distance_from_origin() const;
    int available_distance() const;
    bool operator==(const State &o) const;
    State(): ax(0), bx(0), ay(0), by(0), angle(0), level(0),
          straight(0), turns(0), ups(0), downs(0), pillars(0) {};
    State(int ax, int bx, int ay, int by, int angle, int level,
          int straight, int turns, int ups, int downs, int pillars) :
          ax(ax), bx(bx), ay(ay), by(by), angle(angle), level(level),
          straight(straight), turns(turns), ups(ups), downs(downs),
          pillars(pillars) {};
};

namespace std {
    template <>
    struct hash<State> {
        std::size_t operator()(const State& k) const {
            using std::size_t;
            using std::hash;

            int pos = \
                k.ax ^ (k.bx << 4) ^ (k.ay << 8) ^ (k.by << 12) ^
                (k.angle << 16) ^ (k.level << 20);
            int mat = k.straight ^ (k.turns << 6) ^ (k.ups << 12) ^
                (k.downs << 16) ^ (k.pillars << 20);

            // taken from
            // http://www.boost.org/doc/libs/1_35_0/doc/html/boost/hash_combine_id241013.html 
            int seed = pos;
            seed ^= mat + 0x9e3779b9 + (seed << 6) + (seed >> 2);
            return seed;
        };
    };
}

int State::distance_from_origin() const {
    int astraight = abs(straight);
    int aturns = abs(turns);
    int aups = abs(ups);
    int adowns = abs(downs);
    int apillars = abs(pillars);
    int a1 = astraight > aturns ? astraight: aturns;
    int a2 = aups > adowns ? aups: adowns;
    int a3 = a1 > a2 ? a1: a2;
    return apillars > a3 ? apillars: a3;
}

int State::available_distance() const {
    return straight + turns + ups + downs;
}

bool State::operator==(const State& o) const {
    return ax == o.ax && bx == o.bx && ay == o.ay && by == o.by &&
        angle == o.angle && level == o.level && straight == o.straight &&
        turns == o.turns && ups == o.ups && downs == o.downs &&
        pillars == o.pillars;
}
