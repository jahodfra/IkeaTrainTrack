import unittest

import track


class TestFindSegment(unittest.TestCase):
    def test_segment(self):
        path = 'SRSLS'
        match = 'S'
        res = list(track.Track(path)._find_segments(match))
        self.assertEqual(res, [0, 2, 4])

    def test_wrapped_segment(self):
        path = 'SRSLS'
        match = 'SS'
        res = list(track.Track(path)._find_segments(match))
        self.assertEqual(res, [4])

    def test_no_match(self):
        path = 'SRSLS'
        match = 'US'
        res = list(track.Track(path)._find_segments(match))
        self.assertEqual(res, [])

    def test_all_segments(self):
        path = 'SSS'
        match = 'SSS'
        res = list(track.Track(path)._find_segments(match))
        self.assertEqual(res, [0, 1, 2])


class TestReplaceSegment(unittest.TestCase):
    def test_inside(self):
        path = '0123456789'
        res = track._replace_segment(path, 3, 2, '--')
        self.assertEqual(res, '012--56789')

    def test_start(self):
        path = '0123456789'
        res = track._replace_segment(path, 0, 2, '--')
        self.assertEqual(res, '--23456789')

    def test_end(self):
        path = '0123456789'
        res = track._replace_segment(path, 8, 2, '--')
        self.assertEqual(res, '01234567--')

    def test_wrap(self):
        path = '0123456789'
        res = track._replace_segment(path, 9, 3, '---')
        self.assertEqual(res, '2345678---')


class TestSimplify(unittest.TestCase):
    def test_all_replacements(self):
        path = 'SUSLSU'
        res = list(track.Track(path)._all_replacements('US', 'SU'))
        self.assertEqual(res, ['SSULSU', 'USLSSU'])
    
    def test_shorten_track(self):
        path = 'SRRRRSRRRR'
        res = list(track.Track(path)._shorten_track('S', 'S'))
        self.assertEqual(res, ['RRRRRRRR'])

    def test_shorten_composed_turns(self):
        path = 'RLRRRRLRRRRR'
        res = list(track.Track(path)._shorten_track('RL', 'LR'))
        self.assertEqual(res, ['RRRRRRRR'])

    def test_shorten_horizontal(self):
        path = 'DLLSLRLUDLSLLLSRSLUL'
        res = list(track.Track(path)._shorten_track('S', 'S'))
        self.assertEqual(res, ['DLLLRLUDLSLLLSRLUL'])


class TestPosition(unittest.TestCase):
    def test_angle(self):
        path = 'SRRRRSRRRR'
        res = track.Track(path).angle
        self.assertEqual(res, [0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 0])


if __name__ == '__main__':
    unittest.main()
