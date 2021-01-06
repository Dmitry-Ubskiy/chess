#!/usr/bin/env python3

import curses

from board import Board
from board import parse_move


MOVE_MAX_LEN = 6  # Qd1xg4
MOVE_NR_WIDTH = 4  # Longest chess games ended in under 1000 moves, this is 3 digits + period
MOVE_LOG_LINE_LEN = MOVE_NR_WIDTH + 1 + MOVE_MAX_LEN + 2 + MOVE_MAX_LEN


class Display:
    def __init__(self):
        self._stdscr = curses.initscr()
        curses.start_color()
        self._board_display = self._stdscr.subwin(8, 16, 1, 2)
        self._input_line = self._stdscr.subwin(1, 19, 11, 0)
        self._messages = self._stdscr.subwin(1, 20 + MOVE_LOG_LINE_LEN, 13, 0)

        self._current_move = 1
        self._white_ply = True
        self._move_log = curses.newpad(12, MOVE_LOG_LINE_LEN)

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

    def add_ply(self, ply: str):
        if self._white_ply:
            self._move_log.addstr(self._current_move - 1, 0, f'{self._current_move:3d}. {ply}')
        else:
            self._move_log.addstr(self._current_move - 1, MOVE_LOG_LINE_LEN - MOVE_MAX_LEN, ply)
        self._move_log.refresh(max(0, self._current_move - 12), 0, 0, 20, 12, 20 + MOVE_LOG_LINE_LEN)
        if not self._white_ply:
            self._current_move += 1
            h, w = self._move_log.getmaxyx()
            if self._current_move >= h:
                self._move_log.resize(h + 12, w)
        self._white_ply = not self._white_ply


if __name__ == '__main__':
    board = Board()

    dsp = Display()
    dsp.update_board(board)

    while True:
        move = parse_move(dsp.get_move())
        if not move:
            dsp.show_message('Invalid command!')
            continue
        if board.is_legal_move(move):
            dsp.show_message('')
            formatted_move = repr(board.get_move_canonical_form(move))
            board.make_move(move)
            dsp.update_board(board)
            if board.is_in_check():
                if board.is_mated():
                    formatted_move += '#'
                else:
                    formatted_move += '+'
            dsp.add_ply(formatted_move)
        else:
            dsp.show_message('Illegal move!')

