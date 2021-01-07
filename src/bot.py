#!/usr/bin/env python3

import random

from board import Board, Move

def random_bot(board: Board) -> Move:
    return random.choice(list(board.get_all_legal_moves()))
