import unittest

import dynamic
import solver

def material(straight=0, turns=0, ups=0, downs=0, pillars=0):
    return solver.Material(
        straight=straight, turns=turns, ups=ups, downs=downs, pillars=pillars)

def state_filter(s):
    return s[:5] + s[7:8]

class TestPosition(unittest.TestCase):
    def test_forward_right(self):
        mat = material(turns=8)
        res = dynamic.forward_search(mat)
        res = {state_filter(s) for s in res}
        # circle around -1, with radius 1 (all R)
        self.assertIn((1, 0, 0, -1, 1, 7), res)
        self.assertIn((1, 1, -1, -1, 2, 6), res)
        self.assertIn((1, 0, -2, -1, 3, 5), res)
        self.assertIn((0, 0, -2, -2, 4, 4), res)
        self.assertIn((-1, 0, -2, -1, 5, 3), res)
        self.assertIn((-1, -1, -1, -1, 6, 2), res)
        self.assertIn((-1, 0, 0, -1, 7, 1), res)
        self.assertIn((0, 0, 0, 0, 0, 0), res)

    def test_forward_left(self):
        mat = material(turns=8)
        res = dynamic.forward_search(mat)
        res = {state_filter(s) for s in res}
        # circle around 1, with radius 1 (all L)
        self.assertIn((1, 0, 0, 1, 7, 7), res)
        self.assertIn((1, 1, 1, 1, 6, 6), res)
        self.assertIn((1, 0, 2, 1, 5, 5), res)
        self.assertIn((0, 0, 2, 2, 4, 4), res)
        self.assertIn((-1, 0, 2, 1, 3, 3), res)
        self.assertIn((-1, -1, 1, 1, 2, 2), res)
        self.assertIn((-1, 0, 0, 1, 1, 1), res)
        self.assertIn((0, 0, 0, 0, 0, 0), res)

    def test_find_simple(self):
        mat = material(turns=8)
        res = dynamic.find_all_paths(mat)
        self.assertIn('RRRRRRRR', res)
        self.assertIn('LLLLLLLL', res)

    def test_find_loop(self):
        mat = material(turns=16)
        res = dynamic.find_all_paths(mat)
        self.assertIn('LLRRRRRRRRLLLLLL', res)


if __name__ == '__main__':
    unittest.main()
