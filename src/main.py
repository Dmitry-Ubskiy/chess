#!/usr/bin/env python3

import curses

from enum import Enum
from typing import List

from move import Move, parse_move
from move import Square


class Player(Enum):
    NONE = 0
    WHITE = 1
    BLACK = 2


def format_piece(piece: str, player: Player) -> str:
    if player == Player.WHITE:
        return piece.upper()
    return piece.lower()


def get_piece_owner(piece: str) -> Player:
    if piece.isupper():
        return Player.WHITE
    elif piece.islower():
        return Player.BLACK
    assert piece == '.'
    return Player.NONE  # neither player (empty space)


class Board:
    def __init__(self):
        self._board = sum([
            list('RNBQKBNR'),
            ['P'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['p'] * 8,
            list('rnbqkbnr'),
        ], [])

    def format(self) -> str:
        return '\n'.join(reversed([' '.join(row) for row in zip(*[iter(self._board)]*8)]))

    def at(self, square: Square) -> str:
        return self._board[square._square]

    def valid_moves(self, src: Square) -> List[Square]:
        piece = self._board[src._square]
        if piece == '.':  # empty square
            return []
        owner = get_piece_owner(piece)
        piece = piece.upper()
        dests = []
        if piece == 'P':
            if owner == Player.WHITE:
                assert src._rank != 7
                if self.at(Square(src._file, src._rank+1)) == '.':
                    dests.append(Square(src._file, src._rank+1))
                if src._file > 0 \
                        and self.at(Square(src._file-1, src._rank+1)) != '.' \
                        and get_piece_owner(self.at(Square(src._file-1, src._rank+1))) != owner:
                    dests.append(Square(src._file-1, src._rank+1))
                if src._file < 7 \
                        and self.at(Square(src._file+1, src._rank+1)) != '.' \
                        and get_piece_owner(self.at(Square(src._file+1, src._rank+1))) != owner:
                    dests.append(Square(src._file+1, src._rank+1))
        return dests

    def is_valid_move(self, move: Move, player: Player) -> bool:
        if move.castling is not None:
            return False  # let's not deal with castlings for now
        assert move.dest is not None
        dest_square = Square(move.dest)
        piece = format_piece(move.piece or 'P', player)
        if piece not in self._board:
            return False
        piece_pos = self._board.index(piece)
        possible_pieces_count = 0
        while True:
            if dest_square in self.valid_moves(Square(piece_pos)):
                possible_pieces_count += 1
            if piece not in self._board[piece_pos+1:]:
                break
            piece_pos = self._board.index(piece, piece_pos+1)
        return possible_pieces_count > 0


class Display:
    def __init__(self):
        self._stdscr = curses.initscr()
        curses.start_color()
        self._board_display = self._stdscr.subwin(8, 16, 1, 2)
        self._input_line = self._stdscr.subwin(1, 19, 11, 0)
        self._messages = self._stdscr.subwin(1, 19, 13, 0)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self._stdscr.attron(curses.color_pair(1))
        self._stdscr.addstr(0, 0, '  A B C D E F G H  ')
        self._stdscr.addstr(9, 0, '  A B C D E F G H  ')
        for i, c in enumerate('87654321'):
            self._stdscr.addch(i + 1, 0, c)
            self._stdscr.addch(i + 1, 18, c)
        self._stdscr.refresh()
        self._stdscr.attroff(curses.color_pair(1))

        self._input_line.bkgd(curses.color_pair(1))
        self._input_line.refresh()

    def __del__(self):
        curses.endwin()

    def update_board(self, board: Board):
        self._board_display.addstr(0, 0, board.format())
        self._board_display.refresh()

    def get_move(self) -> str:
        self._input_line.clear()
        self._input_line.addstr(0, 0, '> ')
        return self._input_line.getstr(6).decode('utf-8')

    def show_message(self, message: str):
        self._messages.clear()
        self._messages.addstr(0, 0, message)
        self._messages.refresh()


if __name__ == '__main__':
    board = Board()

    dsp = Display()
    dsp.update_board(board)

    while True:
        move = parse_move(dsp.get_move())
        if not move:
            dsp.show_message('Invalid move!')
            continue
        dsp.show_message(str(board.is_valid_move(move, Player.WHITE)))

