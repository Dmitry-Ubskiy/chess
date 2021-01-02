#!/usr/bin/env python3

import copy
import re

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Set
from typing import overload


class Player(Enum):
    WHITE = 1
    BLACK = 2


def format_piece(piece: str, player: Player) -> str:
    if player == Player.WHITE:
        return piece.upper()
    return piece.lower()


def get_piece_owner(piece: str) -> Optional[Player]:
    if piece.isupper():
        return Player.WHITE
    elif piece.islower():
        return Player.BLACK
    assert piece == '.'
    return None  # neither player (empty space)


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
                raise TypeError('Cannot construct a Square: got "file" but not "rank"')
            file, rank = kwargs['file'], kwargs['rank']
            if file not in range(len(FILES)) or rank not in range(len(RANKS)):
                raise ValueError(f'Not valid square coordinates: "{file, rank}"')
            self._file = file
            self._rank = rank
            self._square = self._rank * 8 + self._file
            self._square_name = Square.SQUARE_NAMES[self._square]
        else:
            raise TypeError('Empty or malformed arguments to Square()')

    def __eq__(self, other: "Square") -> bool:
        if type(other) != Square:
            return False
        return self._square == other._square

    def __add__(self, other: Tuple[int, int]) -> Optional["Square"]:
        df, dr = other
        if Square.valid_square(self._file + df, self._rank + dr):
            return Square(self._file + df, self._rank + dr)
        return None

    def __repr__(self) -> str:
        return self._square_name

    def __hash__(self) -> int:
        return hash(self._square_name)

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
                raise TypeError('Cannot validate a Square: got "file" but not "rank"')
            return kwargs['file'] in range(len(FILES)) and kwargs['rank'] in range(len(RANKS))
        else:
            raise TypeError('Empty or malformed arguments to Square.valid_square()')

    @staticmethod
    def __consolidate_overload_args(args, kwargs) -> dict:
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
            raise TypeError('Too many args passed.')
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

    def __repr__(self):
        if self.castling is not None:
            return self.castling
        assert self.dest is not None
        return ''.join((self.piece or '', self.src or '', self.capture or '', self.dest, self.promotion or ''))


def parse_move(move_notation: str) -> Move:
    # Grammar:
    #      <move> ::= <castling> | <algebraic>
    #  <castling> ::= "0-0" | "0-0-0"
    # <algebraic> ::= <normal> | <promotion>
    #    <normal> ::= (<piece>)? (<src>)? ("x")? <square>
    # <promotion> ::= (<src>)? ("x")? <square> <piece>
    #       <src> ::= <file> | <rank> | <square>
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

    match_src = f'(?:{match_file}|{match_rank}|{match_square})'
    
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


KNIGHT_MOVES = [(-2, -1), (-2, 1), (-1, 2), (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2)]
LATERAL_MOVES = [(-1, 0), (0, -1), (0, 1), (1, 0)]
DIAGONAL_MOVES = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
KING_MOVES = LATERAL_MOVES + DIAGONAL_MOVES

class Board:
    def __init__(self, fen: str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        board_desc, active, castling, en_passant, fifty_move_clock, move_number = fen.split()
        self._board = []
        for c in ''.join(reversed(board_desc.split('/'))):
            if c in '12345678':
                self._board.extend(['.'] * int(c))
            elif c.upper() in PIECES + ['P']:
                self._board.append(c)
            else:
                raise ValueError(f'Character not recognized in FEN board representation: "{c}"')
        if len(self._board) != 64:
            raise ValueError('Malformed FEN board representation: wrong number of total squares')
        self._active_player = Player.WHITE if active == 'w' else Player.BLACK
        self._en_passant = None if en_passant == '-' else Square(en_passant)

    def format(self) -> str:
        return '\n'.join(reversed([' '.join(row) for row in zip(*[iter(self._board)]*8)]))

    def __getitem__(self, square: Square) -> str:
        return self._board[square._square]

    def __setitem__(self, square: Square, value: str):
        self._board[square._square] = value

    def valid_moves(self, src: Square) -> Set[Square]:
        if self[src] == '.':
            return set()
        piece = self[src]
        owner = get_piece_owner(piece)
        opponent = Player.BLACK if owner == Player.WHITE else Player.WHITE
        piece = piece.upper()
        dests = set()

        if piece == 'K':
            for dv in KING_MOVES:  # TODO: self-check
                s = src + dv
                if s is not None:
                    if get_piece_owner(self[s]) != owner:  # empty or opponent's
                        dests.add(s)
        if piece == 'N':
            for dv in KNIGHT_MOVES:
                s = src + dv
                if s is not None:
                    if get_piece_owner(self[s]) != owner:  # empty or opponent's
                        dests.add(s)
        if piece == 'P':
            rank_dir = 1 if owner == Player.WHITE else -1
            push_square = src + (0, rank_dir)
            if push_square is not None and self[push_square] == '.':
                dests.add(push_square)
            for capture_square in [src + (df, rank_dir) for df in (-1, 1)]:
                if capture_square is not None:
                    if capture_square == self._en_passant or get_piece_owner(self[capture_square]) == opponent:
                        dests.add(capture_square)

        def slide(moves: List[Tuple[int, int]]):
            for dv in moves:  # scan in each direction
                next_square = src + dv
                while next_square is not None:
                    controller = get_piece_owner(self[next_square])
                    if controller == owner:
                        break  # inner loop
                    dests.add(next_square)
                    if controller == opponent:
                        break  # inner loop
                    next_square += dv
        if piece == 'R' or piece == 'Q':
            slide(LATERAL_MOVES)
        if piece == 'B' or piece == 'Q':
            slide(DIAGONAL_MOVES)

        return dests

    def __disambiguate_source_squares(self, move: Move) -> Set[Square]:
        assert move.dest is not None
        dest_square = Square(move.dest)
        piece = format_piece(move.piece or 'P', self._active_player)
        if piece not in self._board:
            return set()

        possible_sources = set()
        if move.src is not None:
            if Square.valid_square(move.src):  # explicit, e.g. Ne2g3
                src_square = Square(move.src)
                if self[src_square] == piece and dest_square in self.valid_moves(src_square):
                    return {src_square}
                return set()
            elif move.src in RANKS:  # e.g. N2g3
                rank = move.src
                for file in FILES:
                    src_square = Square(file + rank)
                    if self[src_square] == piece:
                        if dest_square in self.valid_moves(src_square):
                            possible_sources.add(src_square)
            elif move.src in FILES:  # e.g. Neg3
                file = move.src
                for rank in RANKS:
                    src_square = Square(file + rank)
                    if self[src_square] == piece:
                        if dest_square in self.valid_moves(src_square):
                            possible_sources.add(src_square)
            else:
                raise ValueError(f'Malformed move source square: "{move.src}"')
        else:
            piece_index = self._board.index(piece)
            while True:
                src_square = Square(piece_index)
                if dest_square in self.valid_moves(src_square):
                    possible_sources.add(src_square)
                if piece not in self._board[piece_index+1:]:
                    break
                piece_index = self._board.index(piece, piece_index+1)
        return possible_sources

    def is_valid_move(self, move: Move) -> bool:
        if move.castling is not None:
            return False  # let's not deal with castlings for now
        assert move.dest is not None
        return len(self.__disambiguate_source_squares(move)) == 1

    def disambiguate_move(self, move: Move) -> Move:
        assert self.is_valid_move(move)
        new_move = copy.copy(move)
        if new_move.castling is not None:
            return new_move
        new_move.src = next(iter(self.__disambiguate_source_squares(move)))._square_name
        return new_move
