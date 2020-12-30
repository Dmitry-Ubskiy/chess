#!/usr/bin/env python3

import curses

from dataclasses import dataclass
from typing import Optional


@dataclass
class Move:
    piece: str
    to_x: int
    to_y: int


class Board:
    def __init__(self):
        self._board = [
            list('rnbqkbnr'),
            ['p'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['P'] * 8,
            list('RNBQKBNR'),
        ]

    def format(self):
        return '\n'.join(' '.join(row) for row in self._board)


class Display:
    def __init__(self):
        self._stdscr = curses.initscr()
        curses.start_color()
        self._board_display = self._stdscr.subwin(8, 16, 1, 2)
        self._input_line = self._stdscr.subwin(1, 19, 11, 0)

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

    def get_command(self) -> str:
        self._input_line.clear()
        self._input_line.addstr(0, 0, '> ')
        return self._input_line.getstr(3).decode('utf-8')


def parse_command(cmd: str) -> Optional[Move]:
    cmd = cmd.strip().lower()

    if len(cmd) < 2:
        return None
    
    piece = 'p'
    if len(cmd) == 3:
        piece = cmd[0]
        if piece not in 'rnbkqp':
            return None
        cmd = cmd[1:]

    if len(cmd) == 2:
        x, y = cmd
        if x not in 'abcdefgh':
            return None
        if y not in '12345678':
            return None
        return Move(piece, 'abcdefgh'.index(x), '12345678'.index(y))

    return None


if __name__ == '__main__':
    board = Board()

    dsp = Display()
    dsp.update_board(board)

    while True:
        cmd = parse_command(dsp.get_command())
        if cmd is None:
            continue


