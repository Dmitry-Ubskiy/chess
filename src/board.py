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


def get_opponent(player: Player) -> Player:
    if player == Player.WHITE:
        return Player.BLACK
    return Player.WHITE


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

    def __eq__(self, other) -> bool:
        if type(other) != Square:
            return False
        return self._square == other._square

    def __add__(self, other: Tuple[int, int]) -> Optional["Square"]:
        df, dr = other
        if Square.valid_square(self._file + df, self._rank + dr):
            return Square(self._file + df, self._rank + dr)
        return None

    def __sub__(self, other: Tuple[int, int]) -> Optional["Square"]:
        df, dr = other
        if Square.valid_square(self._file - df, self._rank - dr):
            return Square(self._file - df, self._rank - dr)
        return None

    def __repr__(self) -> str:
        return self._square_name

    def __hash__(self) -> int:
        return hash(self._square_name)

    def dist(self, other: "Square") -> int:
        # L_oo
        return max(abs(self._file - other._file), abs(self._rank - other._rank))

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

    def __hash__(self) -> int:
        return hash(repr(self))


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

PUSH_DIRECTION = {Player.WHITE: 1, Player.BLACK: -1}
PLAYER_ABBR = {'w': Player.WHITE, 'b': Player.BLACK}
PAWN_RANK = {Player.WHITE: 1, Player.BLACK: 6}  # 0-indexed; rank index 0 == '1'
BACK_RANK = {Player.WHITE: 0, Player.BLACK: 7}  # 0-indexed; rank index 0 == '1'
CASTLING_END_SQUARES = {
    Player.WHITE: {'0-0': ('g1', 'f1'), '0-0-0': ('c1', 'd1')},
    Player.BLACK: {'0-0': ('g8', 'f8'), '0-0-0': ('c8', 'd8')}
}

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

        self._active_player = PLAYER_ABBR[active]

        self._en_passant = None if en_passant == '-' else Square(en_passant)

        self._available_castlings = {'K': None, 'k': None, 'Q': None, 'q': None}
        if castling != '-':
            for c in castling:
                # FIXME detect the rook's actual place in case of 960
                if c == 'K':
                    self._available_castlings['K'] = 'H'
                elif c == 'k':
                    self._available_castlings['k'] = 'h'
                elif c == 'Q':
                    self._available_castlings['Q'] = 'A'
                elif c == 'q':
                    self._available_castlings['q'] = 'a'
                else:
                    raise NotImplementedError()

        self._fifty_move_clock = int(fifty_move_clock)
        self._move_number = int(move_number)

    def format(self) -> str:
        return '\n'.join(reversed([' '.join(row) for row in zip(*[iter(self._board)]*8)]))

    def fen(self) -> str:
        def format_row(row) -> str:
            empty_count = 0
            row_str = ''
            for c in row:
                if c == '.':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += c
            if empty_count > 0:
                row_str += str(empty_count)
            return row_str
        board = '/'.join(reversed([format_row(row) for row in zip(*[iter(self._board)]*8)]))
        active = 'w' if self._active_player == Player.WHITE else 'b'
        castling = ''.join(sorted(k for k, v in self._available_castlings.items() if v is not None)) or '-'
        en_passant = '-' if self._en_passant is None else self._en_passant._square_name
        fifty_move_clock = str(self._fifty_move_clock)
        move_number = str(self._move_number)
        return f'{board} {active} {castling} {en_passant} {fifty_move_clock} {move_number}'

    def __getitem__(self, square: Square) -> str:
        return self._board[square._square]

    def __setitem__(self, square: Square, value: str):
        self._board[square._square] = value

    def __en_passant_pawn(self) -> Square:
        assert self._en_passant is not None
        # We could just subtract the push direction of the active player, but this seems more explicitly correct
        return self._en_passant + (0, PUSH_DIRECTION[get_opponent(self._active_player)])

    def __is_pseudo_legal(self, src: Square, dest: Square) -> bool:
        # pseudo-legal: can move src to dest by basic rules, without considering checks
        if self[src] == '.':
            return False
        if get_piece_owner(self[src]) == get_piece_owner(self[dest]):
            return False  # can't capture own pieces

        if self[src].upper() == 'P':
            src_owner = get_piece_owner(self[src])
            dest_owner = get_piece_owner(self[dest])
            opponent = get_opponent(src_owner)
            if self.__threatens(src, dest) and (dest_owner == opponent or dest == self._en_passant):  # valid capture
                return True
            # pushes
            if dest._file != src._file:
                return False
            if self[src + (0, PUSH_DIRECTION[src_owner])] != '.':
                return False  # blocked
            if src.dist(dest) == 1:  # push
                return dest._rank - src._rank == PUSH_DIRECTION[src_owner]
            elif src.dist(dest) == 2:  # double push
                if src._rank not in (BACK_RANK[src_owner], PAWN_RANK[src_owner]):
                    return False
                if self[dest] != '.':
                    return False  # blocked
                return dest._rank - src._rank == 2 * PUSH_DIRECTION[src_owner]
            else:
                return False  # dest too far
        elif self.__threatens(src, dest):
            return True
        return False

    def __threatens(self, src: Square, dest: Square) -> bool:
        if self[src] == '.':
            return False
        if get_piece_owner(self[src]) == get_piece_owner(self[dest]):
            return False  # can't capture own pieces

        piece = self[src]
        src_owner = get_piece_owner(piece)
        piece = piece.upper()

        if piece == 'K':
            return src.dist(dest) == 1
        if piece == 'N':
            return (dest - (src._file, src._rank)) in KNIGHT_MOVES
        if piece == 'P':
            if src.dist(dest) == 1:  # pawn capture
                if dest._rank - src._rank != PUSH_DIRECTION[src_owner]:
                    return False  # wrong direction
                return abs(dest._file - src._file) == 1
            else:
                return False  # dest too far
        
        if piece == 'R':
            if src._file != dest._file and src._rank != dest._rank:
                return False
        if piece == 'B':
            if abs(src._file - dest._file) != abs(src._rank - dest._rank):
                return False
        if piece == 'Q':
            if src._file != dest._file and src._rank != dest._rank and abs(src._file - dest._file) != abs(src._rank - dest._rank):
                return False

        if piece in ['R', 'B', 'Q']:
            sgn = lambda x: 0 if x == 0 else x//abs(x)
            dv = (sgn(dest._file - src._file), sgn(dest._rank - src._rank))
            next_square = src + dv
            while next_square != dest:
                if self[next_square] != '.':  # obstacle
                    return False
                next_square += dv
            return True  # got to dest with no obstacles

        # should be unreachable
        return False

    def __is_threatened_by(self, square: Square, player: Player) -> bool:
        return any(map(lambda s: get_piece_owner(self[s]) == player, self.__get_square_attackers(square)))

    def __get_square_attackers(self, square: Square) -> Set[Square]:
        attackers = set()
        owner = get_piece_owner(self[square])
        for i, piece in enumerate(self._board):
            if piece == '.' or get_piece_owner(piece) == owner:
                continue
            if self.__threatens(Square(i), square):
                attackers.add(Square(i))
        return attackers

    def is_in_check(self, player: Optional[Player] = None) -> bool:
        if player is None:
            player = self._active_player
        king = format_piece('K', player)
        king_square = Square(self._board.index(king))
        opponent = get_opponent(player)
        return self.__is_threatened_by(king_square, opponent)

    def is_mated(self) -> bool:
        return self.is_in_check() and len(self.get_all_legal_moves()) == 0

    def __is_in_legal_state(self) -> bool:
        # Conditions for board legality:
        # - Two kings: k and K
        # - Opposing player's king is not in check
        if 'k' not in self._board or 'K' not in self._board:
            return False
        if self.is_in_check(get_opponent(self._active_player)):
            return False
        return True

    def __is_legal(self, src: Square, dest: Square) -> bool:
        if not self.__is_pseudo_legal(src, dest):
            return False
        piece = self[src].upper()
        if piece == 'P':
            piece = None
        aftermath = self.make_move_copy(Move(piece=piece, src=src._square_name, dest=dest._square_name))
        return aftermath.__is_in_legal_state()

    def is_legal_move(self, move: Move) -> bool:
        if move.castling is not None:
            if move.castling not in CASTLINGS:
                raise ValueError(f'Malformed castling designation: "{move.castling}"')
            if self.is_in_check():  # starting in check
                return False
            opponent = get_opponent(self._active_player)
            for s in CASTLING_END_SQUARES[self._active_player][move.castling]:  # moving through / ending in check
                if self.__is_threatened_by(Square(s), opponent):
                    return False

            king = format_piece('K', self._active_player)
            king_square = Square(self._board.index(king))

            side = format_piece('K' if move.castling == '0-0' else 'Q', self._active_player)
            if self._available_castlings[side] is None:
                return False
            rook_file = self._available_castlings[side].lower()
            rank = '1' if self._active_player == Player.WHITE else '8'
            rook_square = Square(rook_file + rank)

            # span of squares between the king and the rook
            span = king_square._square, rook_square._square
            span = min(span) + 1, max(span)
            return all(map(lambda s: self[Square(s)] == '.', range(*span)))

        assert move.dest is not None
        dest_square = Square(move.dest)
        if move.capture is not None:  # if you say you capture, you better actually capture something
            if get_piece_owner(self[dest_square]) != get_opponent(self._active_player):  # not normal capture...
                if move.piece is not None or self._en_passant != dest_square:  # ...nor en passant...
                    return False  # ...so this move isn't legal!
        possible_sources = self.__disambiguate_source_squares(move)
        if len(self.__disambiguate_source_squares(move)) != 1:
            return False
        src_square = next(iter(possible_sources))
        piece = self[src_square].upper()
        if piece != move.piece and not (move.piece is None and piece == 'P'):
            return False
        return self.__is_legal(src_square, dest_square)

    def legal_moves(self, src: Square) -> Set[Square]:
        if self[src] == '.':
            return set()
        piece = self[src]
        owner = get_piece_owner(piece)
        piece = piece.upper()
        dests = set()

        if piece == 'K':
            for dv in KING_MOVES:
                s = src + dv
                if s is not None:
                    if self.__is_legal(src, s):
                        dests.add(s)

        if piece == 'N':
            for dv in KNIGHT_MOVES:
                s = src + dv
                if s is not None:
                    if self.__is_legal(src, s):
                        dests.add(s)
        if piece == 'P':
            push_dir = PUSH_DIRECTION[owner]
            push_square = src + (0, push_dir)
            if push_square is not None and self.__is_legal(src, push_square):
                dests.add(push_square)
            # double push; works if pawns can start on 1st rank (double push from original position or 2nd rank)
            if src._rank in (BACK_RANK[owner], PAWN_RANK[owner]):
                double_push_square = push_square + (0, push_dir)
                if double_push_square is not None and self.__is_legal(src, double_push_square):
                    dests.add(double_push_square)
            for capture_square in [src + (df, push_dir) for df in (-1, 1)]:
                if capture_square is not None:
                    if self.__is_legal(src, capture_square):
                        dests.add(capture_square)

        def slide(moves: List[Tuple[int, int]]):
            for dv in moves:  # scan in each direction
                next_square = src + dv
                while next_square is not None:
                    if self.__is_legal(src, next_square):
                        dests.add(next_square)
                    next_square += dv
        if piece == 'R' or piece == 'Q':
            slide(LATERAL_MOVES)
        if piece == 'B' or piece == 'Q':
            slide(DIAGONAL_MOVES)

        return dests

    def get_all_legal_moves(self) -> Set[Move]:
        moves = set()
        for c in CASTLINGS:
            if self.is_legal_move(parse_move(c)):
                moves.add(parse_move(c))
        for i, piece in enumerate(self._board):
            if get_piece_owner(piece) != self._active_player:
                continue
            move_piece = piece.upper()
            if move_piece == 'P':
                move_piece = None
            if move_piece is None and Square(i)._rank == PAWN_RANK[get_opponent(self._active_player)]:  # generate promotions for each move
                moves |= {  
                    Move(piece=move_piece, src=Square(i)._square_name, dest=s._square_name, promotion=promotion)
                    for s in self.legal_moves(Square(i)) for promotion in 'RBNQ'
                }
            else:
                moves |= {Move(piece=move_piece, src=Square(i)._square_name, dest=s._square_name) for s in self.legal_moves(Square(i))}
        return moves

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
                if self[src_square] == piece:
                    return {src_square}
                return set()
            elif move.src in RANKS:  # e.g. N2g3
                rank = move.src
                for file in FILES:
                    src_square = Square(file + rank)
                    if self[src_square] == piece:
                        if dest_square in self.legal_moves(src_square):
                            possible_sources.add(src_square)
            elif move.src in FILES:  # e.g. Neg3
                file = move.src
                for rank in RANKS:
                    src_square = Square(file + rank)
                    if self[src_square] == piece:
                        if dest_square in self.legal_moves(src_square):
                            possible_sources.add(src_square)
            else:
                raise ValueError(f'Malformed move source square: "{move.src}"')
        else:
            piece_index = self._board.index(piece)
            while True:
                src_square = Square(piece_index)
                if dest_square in self.legal_moves(src_square):
                    possible_sources.add(src_square)
                if piece not in self._board[piece_index+1:]:
                    break
                piece_index = self._board.index(piece, piece_index+1)
        return possible_sources

    def disambiguate_move(self, move: Move) -> Move:
        new_move = copy.copy(move)
        if new_move.castling is not None:
            return new_move
        new_move.src = next(iter(self.__disambiguate_source_squares(move)))._square_name
        if self[Square(new_move.dest)] != '.':
            new_move.capture = 'x'
        elif new_move.piece is None and Square(new_move.dest) == self._en_passant:  # en passant capture
            new_move.capture = 'x'
        return new_move

    def get_move_canonical_form(self, move: Move) -> Move:
        maximal_form = self.disambiguate_move(move)
        canonical_move = copy.copy(maximal_form)
        if canonical_move.castling is not None:
            return canonical_move
        # minimize src
        src_addr = maximal_form.src
        src_file, src_rank = src_addr
        for src in (None, src_file, src_rank, src_addr):
            if canonical_move.piece is None and canonical_move.capture is not None:  # pawn capture
                if src is None:  # pawn captures should specify the file the capture is from
                    continue
            canonical_move.src = src
            if self.is_legal_move(canonical_move):
                break
        return canonical_move

    def make_move(self, move: Move):
        if move.castling is not None:
            side = format_piece('K' if move.castling == '0-0' else 'Q', self._active_player)

            rank = '1' if self._active_player == Player.WHITE else '8'
            rook_file = self._available_castlings[side].lower()
            rook_square = Square(rook_file + rank)

            king = format_piece('K', self._active_player)
            king_square = Square(self._board.index(king))

            self[king_square] = '.'
            self[rook_square] = '.'

            # in every variation (classic, Fischer, really bad chess) the ending squares are the same
            king_end_square, rook_end_square = CASTLING_END_SQUARES[self._active_player][move.castling]
            self[Square(king_end_square)] = king
            self[Square(rook_end_square)] = format_piece('R', self._active_player)

            for side in [format_piece(s, self._active_player) for s in 'KQ']:
                self._available_castlings[side] = None

            self._fifty_move_clock += 1
        else:
            disambiguated_move = self.disambiguate_move(move)

            src_square = Square(disambiguated_move.src)
            dest_square = Square(disambiguated_move.dest)

            if disambiguated_move.piece is None and dest_square == self._en_passant:  # en passant capture
                self[self.__en_passant_pawn()] = '.'

            self._en_passant = None
            if move.piece is None and abs(src_square._rank - dest_square._rank) == 2:  # double push
                self._en_passant = Square(src_square._file, (src_square._rank + dest_square._rank) // 2)

            self[dest_square] = self[src_square]
            self[src_square] = '.'

            if move.piece is None and dest_square._rank == BACK_RANK[get_opponent(self._active_player)]:
                promotion = format_piece(move.promotion or 'Q', self._active_player)
                self[dest_square] = promotion

            if move.piece == 'K':
                for side in [format_piece(s, self._active_player) for s in 'KQ']:
                    self._available_castlings[side] = None
            elif move.piece == 'R':
                if src_square._rank == BACK_RANK[self._active_player]:
                    castling_file = format_piece(FILES[src_square._file], self._active_player)
                    for side in list(self._available_castlings):
                        if self._available_castlings[side] == castling_file:
                            self._available_castlings[side] = None
                
                self._fifty_move_clock += 1

        self._active_player = get_opponent(self._active_player)
        if self._active_player == Player.WHITE:
            self._move_number += 1

    def make_move_copy(self, move: Move) -> "Board":
        new_board = copy.deepcopy(self)
        new_board.make_move(move)
        return new_board

    def _flip_player_copy(self) -> "Board":
        new_board = copy.deepcopy(self)
        new_board._active_player = get_opponent(self._active_player)
        return new_board
