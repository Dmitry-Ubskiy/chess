#!/usr/bin/env python3

import re

from dataclasses import dataclass
from typing import Optional, overload


CASTLINGS = ('0-0', '0-0-0')
PIECES = list('RNBQK')
FILES = list('abcdefgh')
RANKS = list('12345678')


class Square:
    SQUARE_NAMES = [''.join((f, r)) for r in RANKS for f in FILES]

    @overload
    def __init__(self, square_name: str):
        ...

    @overload
    def __init__(self, square_index: int):
        ...

    @overload
    def __init__(self, file: int, rank: int):
        ...

    def __init__(self, *args, **kwargs):
        kwargs = Square.__consolidate_overload_args(args, kwargs)

        if 'square_name' in kwargs:
            square_name = kwargs['square_name']
            self._square_name = square_name.lower()
            if self._square_name not in Square.SQUARE_NAMES:
                raise ValueError(f'Not a valid square name: "{square_name}"')
            self._file = FILES.index(self._square_name[0])
            self._rank = RANKS.index(self._square_name[1])
            self._square = self._rank * 8 + self._file
        elif 'square_index' in kwargs:
            square_index = kwargs['square_index']
            if square_index not in range(len(Square.SQUARE_NAMES)):
                raise ValueError(f'Not a valid square index: "{square_index}"')
            self._square = square_index
            self._square_name = Square.SQUARE_NAMES[self._square]
            self._file = FILES.index(self._square_name[0])
            self._rank = RANKS.index(self._square_name[1])
        elif 'file' in kwargs:
            if 'rank' not in kwargs:
                raise TypeError()
            file, rank = kwargs['file'], kwargs['rank']
            if file not in range(len(FILES)) or rank not in range(len(RANKS)):
                raise ValueError(f'Not valid square coordinates: "{file, rank}"')
            self._file = file
            self._rank = rank
            self._square = self._rank * 8 + self._file
            self._square_name = Square.SQUARE_NAMES[self._square]
        else:
            raise TypeError()

    def __eq__(self, other):
        return self._square == other._square

    @staticmethod
    @overload
    def valid_square(square_name: str) -> bool:
        ...

    @staticmethod
    @overload
    def valid_square(square_index: int) -> bool:
        ...

    @staticmethod
    @overload
    def valid_square(file: int, rank: int) -> bool:
        ...

    @staticmethod
    def valid_square(*args, **kwargs) -> bool:
        kwargs = Square.__consolidate_overload_args(args, kwargs)

        if 'square_name' in kwargs:
            return kwargs['square_name'] in Square.SQUARE_NAMES
        elif 'square_index' in kwargs:
            return kwargs['square_index'] in range(len(Square.SQUARE_NAMES))
        elif 'file' in kwargs:
            if 'rank' not in kwargs:
                raise TypeError()
            return kwargs['file'] in range(len(FILES)) and kwargs['rank'] in range(len(RANKS))
        else:
            raise TypeError()

    @staticmethod
    def __consolidate_overload_args(args, kwargs):
        if len(args) == 0:
            pass  # straight to kwargs
        elif len(args) == 1:
            if type(args[0]) == str:
                assert not kwargs
                kwargs['square_name'] = args[0]
            elif type(args[0]) == int:
                if 'file' in kwargs:
                    assert 'rank' not in kwargs
                    kwargs['rank'] = args[0]
                elif 'rank' in kwargs:
                    kwargs['file'] = args[0]
                else:
                    assert not kwargs
                    kwargs['square_index'] = args[0]
        elif len(args) == 2:  # (file, rank)
            assert not kwargs
            kwargs['file'], kwargs['rank'] = args
        else:
            raise TypeError()
        return kwargs


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
