#!/usr/bin/env python3

from time import time

from datetime import timedelta

import tqdm

from board import Board, Player
from board import parse_move
from bot import random_bot, dummy_bot, minmax_bot


def run_bot_game(bot, plies=100, max_time=60):
    board = Board()

    start = time()
    for _ in tqdm.tqdm(range(plies), desc=bot.__name__):
        board.make_move(bot(board))
        if board.is_mated():
            board = Board()
        if time() - start > max_time:
            break


def main():
    run_bot_game(random_bot)
    run_bot_game(dummy_bot)
    run_bot_game(minmax_bot)


if __name__ == '__main__':
    main()
