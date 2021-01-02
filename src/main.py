#!/usr/bin/env python3

import curses

from board import Board, Player
from board import parse_move


class Display:
    def __init__(self):
        self._stdscr = curses.initscr()
        curses.start_color()
        self._board_display = self._stdscr.subwin(8, 16, 1, 2)
        self._input_line = self._stdscr.subwin(1, 19, 11, 0)
        self._messages = self._stdscr.subwin(1, 19, 13, 0)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self._stdscr.attron(curses.color_pair(1))
        self._stdscr.addstr(0, 0, '  a b c d e f g h  ')
        self._stdscr.addstr(9, 0, '  a b c d e f g h  ')
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
            dsp.show_message('Invalid move fmt!')
            continue
        if board.is_valid_move(move):
            dsp.show_message(repr(board.disambiguate_move(move)))
        else:
            dsp.show_message('Invalid move!')

