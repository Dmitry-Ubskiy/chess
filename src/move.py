#!/usr/bin/env python3

import re

from dataclasses import dataclass
from typing import Optional


CASTLINGS = ('0-0', '0-0-0')
PIECES = list('RNBQK')
FILES = list('abcdefgh')
RANKS = list('12345678')


class Square:
    SQUARES = list(range(64))
    SQUARE_NAMES = [''.join((f, r)) for f in FILES for r in RANKS]

    def __init__(self, square_name: str):
        self._square_name = square_name.lower()
        if self._square_name not in Square.SQUARE_NAMES:
            raise ValueError(f'Not a valid square name: "{square_name}"')
        self._file = 'abcdefgh'.index(self._square_name[0])
        self._rank = '12345678'.index(self._square_name[1])
        self._square = self._file * 8 + self._rank

    @staticmethod
    def valid_square(square_name):
        return square_name in Square.SQUARE_NAMES


@dataclass
class Move:
    castling: Optional[str] = None
    capture: Optional[str] = None
    piece: Optional[str] = None
    src: Optional[str] = None
    dest: Optional[str] = None
    promotion: Optional[str] = None
    
    def __bool__(self):
        return self.castling is not None or self.dest is not None


def parse_move(move_notation: str) -> Move:
        # Grammar:
        #      <move> ::= <castling> | <algebraic>
        #  <castling> ::= "0-0" | "0-0-0"
        # <algebraic> ::= <normal> | <promotion>
        #    <normal> ::= (<piece>)? (<src>)? ("x")? <square>
        # <promotion> ::= (<src>)? ("x")? <square> <piece>
        #      <src> ::= <file> | <square>
        #    <square> ::= <file> <rank>
        #     <piece> ::= "R" | "N" | "B" | "Q" | "K"
        #      <file> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h"
        #      <rank> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8"

        if move_notation in CASTLINGS:
            return Move(castling=move_notation)

        match_piece = f'[{"".join(PIECES)}]'
        match_file = f'[{"".join(FILES)}]'
        match_rank = f'[{"".join(RANKS)}]'
        match_square = f'{match_file}{match_rank}'

        match_src = f'(?:{match_file}|{match_square})'
        
        match_common = f'(?P<src>{match_src})?(?P<capture>x)?(?P<dest>{match_square})'
        match_normal = f'(?P<piece>{match_piece})?{match_common}$'
        match_promotion = f'{match_common}(?P<promotion>{match_piece})?$'

        normal_move = re.match(match_normal, move_notation)
        if normal_move is not None:
            return Move(**normal_move.groupdict())

        promotion_move = re.match(match_promotion, move_notation)
        if promotion_move is not None:
            return Move(**promotion_move.groupdict())

        return Move()
