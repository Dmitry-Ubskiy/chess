#!/usr/bin/env python3

import re

from typing import Optional, Mapping


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


def _parse_algebraic_notation(move_notation: str) -> Optional[Mapping[str, str]]:
        # Grammar:
        #      <move> ::= <castling> | <algebraic>
        #  <castling> ::= "0-0" | "0-0-0"
        # <algebraic> ::= <normal> | <promotion>
        #    <normal> ::= (<piece>)? (<from>)? ("x")? <square>
        # <promotion> ::= (<from>)? ("x")? <square> <piece>
        #      <from> ::= <file> | <square>
        #    <square> ::= <file> <rank>
        #     <piece> ::= "R" | "N" | "B" | "Q" | "K"
        #      <file> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h"
        #      <rank> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8"

        if move_notation in CASTLINGS:
            return {'castling': move_notation}

        match_piece = f'[{"".join(PIECES)}]'
        match_file = f'[{"".join(FILES)}]'
        match_rank = f'[{"".join(RANKS)}]'
        match_square = f'{match_file}{match_rank}'

        match_from = f'(?:{match_file}|{match_square})'
        
        match_common = f'(?P<from>{match_from})?(?P<capture>x)?(?P<to>{match_square})'
        match_normal = f'(?P<piece>{match_piece})?{match_common}$'
        match_promotion = f'{match_common}(?P<promotion>{match_piece})?$'

        normal_move = re.match(match_normal, move_notation)
        if normal_move is not None:
            return normal_move.groupdict()

        promotion_move = re.match(match_promotion, move_notation)
        if promotion_move is not None:
            return promotion_move.groupdict()

        return None


class Move:
    def __init__(self, move_notation: str):
        parsed_move = _parse_algebraic_notation(move_notation)
        if parsed_move is None:
            raise ValueError(f'Not a valid move: "{move_notation}"')
        self._castling = parsed_move.get('castling', None)
        self._piece = parsed_move.get('piece', None)
        self._from = parsed_move.get('from', None)
        self._to = parsed_move.get('to', None)
        self._promotion = parsed_move.get('promotion', None)

    @staticmethod
    def is_valid_notation(move_notation: str):
        return _parse_algebraic_notation(move_notation) is not None
