#!/usr/bin/env python3

import unittest

from board import Board, Square


class MoveTest(unittest.TestCase):
    def test_knight_moves(self):
        board = Board('8/8/8/4N3/8/8/8/8 w - - 0 1')
        self.assertSetEqual(
            board.valid_moves(Square('e5')),
            set(map(Square, ['d3', 'f3', 'g4', 'g6', 'f7', 'd7', 'c6', 'c4']))
        )

    def test_sliding_moves(self):
        board = Board('8/8/8/4B3/8/2q1R3/8/8 w - - 0 1')
        self.assertSetEqual(
            board.valid_moves(Square('e5')),
            set(map(Square, ['d6', 'c7', 'b8', 'f6', 'g7', 'h8', 'f4', 'g3', 'h2', 'd4', 'c3']))
        )
        self.assertSetEqual(
            board.valid_moves(Square('e3')),
            set(map(Square, ['d3', 'c3', 'e4', 'f3', 'g3', 'h3', 'e2', 'e1']))
        )
        self.assertSetEqual(
            board.valid_moves(Square('c3')),
            set(map(Square, [
                'c4', 'c5', 'c6', 'c7', 'c8', 'd3', 'e3', 'c2', 'c1', 'b3', 'a3',  # lateral
                'd4', 'e5', 'd2', 'e1', 'b2', 'a1', 'b4', 'a5'  # diagonal
            ]))
        )

    def test_pawn_moves(self):
        board = Board('8/8/8/6pP/8/8/4P3/8 w - g6 0 1')
        self.assertSetEqual(
            board.valid_moves(Square('h5')),
            set(map(Square, ['h6', 'g6']))
        )
        self.assertSetEqual(
            board.valid_moves(Square('e2')),
            set(map(Square, ['e3', 'e4']))
        )

    def test_king_moves(self):
        board = Board('8/8/8/3k4/5K2/8/8/8 w - g6 0 1')
        self.assertSetEqual(
            board.valid_moves(Square('d5')),
            set(map(Square, ['c6', 'd6', 'e6', 'd4', 'c4', 'c5']))
        )
        self.assertSetEqual(
            board.valid_moves(Square('f4')),
            set(map(Square, ['f5', 'g5', 'g4', 'g3', 'f3', 'e3']))
        )


if __name__ == '__main__':
    unittest.main()
