#!/usr/bin/env python3

import unittest

from board import Board, Square, Move
from board import parse_move


class MoveTest(unittest.TestCase):
    def test_knight_moves(self):
        board = Board('8/8/8/4N3/8/8/8/k6K w - - 0 1')
        self.assertSetEqual(
            board.legal_moves(Square('e5')),
            set(map(Square, ['d3', 'f3', 'g4', 'g6', 'f7', 'd7', 'c6', 'c4']))
        )

    def test_sliding_moves(self):
        board = Board('8/8/8/4B3/8/2q1R3/8/1k5K w - - 0 1')
        self.assertSetEqual(
            board.legal_moves(Square('e5')),
            set(map(Square, ['d6', 'c7', 'b8', 'f6', 'g7', 'h8', 'f4', 'g3', 'h2', 'd4', 'c3']))
        )
        self.assertSetEqual(
            board.legal_moves(Square('e3')),
            set(map(Square, ['d3', 'c3', 'e4', 'f3', 'g3', 'h3', 'e2', 'e1']))
        )
        board = Board('8/8/8/4B3/8/2q1R3/8/1k5K b - - 0 1')
        self.assertSetEqual(
            board.legal_moves(Square('c3')),
            set(map(Square, [
                'c4', 'c5', 'c6', 'c7', 'c8', 'd3', 'e3', 'c2', 'c1', 'b3', 'a3',  # lateral
                'd4', 'e5', 'd2', 'e1', 'b2', 'a1', 'b4', 'a5'  # diagonal
            ]))
        )

    def test_pawn_moves(self):
        board = Board('k6K/8/8/6pP/8/8/4P3/8 w - g6 0 1')
        self.assertSetEqual(
            board.legal_moves(Square('h5')),
            set(map(Square, ['h6', 'g6']))
        )
        self.assertSetEqual(
            board.legal_moves(Square('e2')),
            set(map(Square, ['e3', 'e4']))
        )

        board = Board('6b1/7P/8/8/8/8/r7/kr4BK w - - 0 1')
        self.assertSetEqual(
            board.get_all_legal_moves(),
            set(map(parse_move, ['h7' + dest + prom for dest in ('h8', 'g8') for prom in 'RBNQ']))
        )

    def test_king_moves(self):
        board = Board('8/8/8/3k4/5K2/8/8/8 b - - 0 1')
        self.assertSetEqual(
            board.legal_moves(Square('d5')),
            set(map(Square, ['c6', 'd6', 'e6', 'd4', 'c4', 'c5']))
        )
        board = Board('8/8/8/3k4/5K2/8/8/8 w - - 0 1')
        self.assertSetEqual(
            board.legal_moves(Square('f4')),
            set(map(Square, ['f5', 'g5', 'g4', 'g3', 'f3', 'e3']))
        )


class CastlingTest(unittest.TestCase):
    def test_normal(self):
        board = Board('r3k3/8/8/8/8/8/8/4K2R w Kq - 0 1')
        
        self.assertTrue(board.is_legal_move(Move(castling='0-0')))
        self.assertFalse(board.is_legal_move(Move(castling='0-0-0')))

        board.make_move(Move(castling='0-0'))
        self.assertEqual(board.fen(), 'r3k3/8/8/8/8/8/8/5RK1 b q - 1 1')

        self.assertFalse(board.is_legal_move(Move(castling='0-0')))
        self.assertTrue(board.is_legal_move(Move(castling='0-0-0')))

        board.make_move(Move(castling='0-0-0'))
        self.assertEqual(board.fen(), '2kr4/8/8/8/8/8/8/5RK1 w - - 2 2')

    def test_move(self):
        board = Board('4k3/8/8/8/8/8/8/R3K2R w KQq - 0 1')
        
        self.assertTrue(board.is_legal_move(Move(castling='0-0')))
        self.assertTrue(board.is_legal_move(Move(castling='0-0-0')))

        kings_rook_moved = board.make_move_copy(parse_move('Rh1h2')).make_move_copy(parse_move('Ke7'))
        self.assertFalse(kings_rook_moved.is_legal_move(Move(castling='0-0')))
        self.assertTrue(kings_rook_moved.is_legal_move(Move(castling='0-0-0')))

        queens_rook_moved = board.make_move_copy(parse_move('Ra1b1')).make_move_copy(parse_move('Ke7'))
        self.assertTrue(queens_rook_moved.is_legal_move(Move(castling='0-0')))
        self.assertFalse(queens_rook_moved.is_legal_move(Move(castling='0-0-0')))

        king_moved = board.make_move_copy(parse_move('Ke1d1')).make_move_copy(parse_move('Ke7'))
        self.assertFalse(king_moved.is_legal_move(Move(castling='0-0')))
        self.assertFalse(king_moved.is_legal_move(Move(castling='0-0-0')))

    def test_blocked(self):
        board = Board('4k3/8/8/8/8/8/8/RN2K2R w KQq - 0 1')

        self.assertTrue(board.is_legal_move(Move(castling='0-0')))
        self.assertFalse(board.is_legal_move(Move(castling='0-0-0')))

    def test_check(self):
        board = Board('4k3/8/8/8/8/8/4r3/R3K3 w Q - 0 1')  # king in check
        self.assertFalse(board.is_legal_move(Move(castling='0-0-0')))

        board = Board('4k3/8/8/8/8/8/3r4/R3K3 w Q - 0 1')  # pass through check
        self.assertFalse(board.is_legal_move(Move(castling='0-0-0')))

        board = Board('4k3/8/8/8/8/8/2r5/R3K3 w Q - 0 1')  # end in check
        self.assertFalse(board.is_legal_move(Move(castling='0-0-0')))


class DiscoveredCheckTest(unittest.TestCase):
    def test_en_passant(self):
        board = Board('8/8/8/8/k2Pp2Q/8/8/3K4 b - d3 0 1')
        self.assertFalse(board.is_legal_move(Move(src='e4', dest='d3')))


if __name__ == '__main__':
    unittest.main()
