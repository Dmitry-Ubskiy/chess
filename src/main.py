#!/usr/bin/env python3

import curses


from move import Move



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

    def get_move(self) -> str:
        self._input_line.clear()
        self._input_line.addstr(0, 0, '> ')
        return self._input_line.getstr(6).decode('utf-8')


if __name__ == '__main__':
    board = Board()

    dsp = Display()
    dsp.update_board(board)

    while True:
        move = dsp.get_move()
        if not Move.is_valid_notation(move):
            continue
        break

