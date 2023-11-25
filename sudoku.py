"""A simple and fast Sudoku solver."""

import enum
import sys
from typing import Sequence, Self

R_TO_NUM = {0: 0, 1: 1, 2: 2, 4: 3, 8: 4, 16: 5, 32: 6, 64: 7, 128: 8, 256: 9}
FULL_MASK = 0x1FF


class SolverResults(enum.Enum):
  """Solver outcomes."""
  NO_UPDATE = 0
  UPDATE = 1
  CONFLICT = 2
  ALL_DONE = 3


class Slot():
  """Representation of a slot in sudoku."""

  def __init__(self, number: int = 0) -> None:
    self.set(number)

  def set(self, number: int):
    """Fills a number to the slot."""
    self.raw = 1 << (number - 1) if number else 0

  @property
  def is_fill(self) -> int:
    """Checks if the slot is filled."""
    return int(self.raw != 0)

  def __int__(self) -> int:
    return R_TO_NUM[self.raw]

  def __str__(self) -> str:
    return str(int(self))

  def __repr__(self) -> str:
    return str(self)


class SlotGroup():
  """Representation of a group of slots."""

  def __init__(self, s1: Slot, s2: Slot, s3: Slot, s4: Slot, s5: Slot, s6: Slot,
               s7: Slot, s8: Slot, s9: Slot) -> None:
    self.s1: Slot = s1
    self.s2: Slot = s2
    self.s3: Slot = s3
    self.s4: Slot = s4
    self.s5: Slot = s5
    self.s6: Slot = s6
    self.s7: Slot = s7
    self.s8: Slot = s8
    self.s9: Slot = s9

  @property
  def combine(self) -> int:
    return (self.s1.raw | self.s2.raw | self.s3.raw | self.s4.raw |
            self.s5.raw | self.s6.raw | self.s7.raw | self.s8.raw | self.s9.raw)

  @property
  def is_legal(self) -> bool:
    return self.combine.bit_count() == (self.s1.is_fill + self.s2.is_fill +
                                        self.s3.is_fill + self.s4.is_fill +
                                        self.s5.is_fill + self.s6.is_fill +
                                        self.s7.is_fill + self.s8.is_fill +
                                        self.s9.is_fill)

  def __str__(self) -> str:
    return (f'{self.s1}{self.s2}{self.s3} '
            f'{self.s4}{self.s5}{self.s6} '
            f'{self.s7}{self.s8}{self.s9}')

  def __repr__(self) -> str:
    return str(self)


class SlotCandidates():
  """Representation of all possible choices of a given slot."""

  def __init__(self, gp1: SlotGroup, gp2: SlotGroup, gp3: SlotGroup) -> None:
    self.raw = FULL_MASK - (gp1.combine | gp2.combine | gp3.combine)
    self._ind = 0

  def __len__(self) -> int:
    return self.raw.bit_count()

  def __iter__(self) -> Self:
    self._ind = 0
    return self

  def __next__(self) -> int:
    if self._ind > 8:
      raise StopIteration
    mask = 1 << self._ind
    self._ind += 1
    if mask & self.raw:
      return mask
    else:
      return self.__next__()


class SudokuBoard():
  """Representation of one Sudoku board."""

  def __init__(self) -> None:
    """Books a new RAM space for holding the Sudoku puzzle."""
    self.board = [[Slot() for _ in range(9)] for _ in range(9)]
    self.row = [SlotGroup(*self.board[i]) for i in range(9)]
    self.column = [SlotGroup(*[r[i] for r in self.board]) for i in range(9)]
    self.block: list[SlotGroup] = []
    for i in [0, 3, 6]:
      for r in [0, 3, 6]:
        self.block.append(
            SlotGroup(*self.board[i][r:r + 3], *self.board[i + 1][r:r + 3],
                      *self.board[i + 2][r:r + 3]))
    self.empty_slots: list[tuple[int, int]] = []

  def set_board_num(self, board: Sequence[Sequence[int]]) -> None:
    """Inits board with a 2-D array."""
    self.empty_slots = []
    for r, (rowslot, row) in enumerate(zip(self.board, board)):
      for c, (slot, num) in enumerate(zip(rowslot, row)):
        if num == 0:
          self.empty_slots.append((r, c))
        slot.set(num)

  def sync_to(self, ref: Self) -> None:
    """Syncs this board to another SudokuBoard."""
    self.board = ref.board
    self.row = ref.row
    self.column = ref.column
    self.block = ref.block
    self.empty_slots = ref.empty_slots

  def clone(self) -> Self:
    """Generates a clone of this board."""
    new_board = SudokuBoard()
    for rowslot, row in zip(new_board.board, self.board):
      for slot, num in zip(rowslot, row):
        slot.raw = num.raw
    new_board.empty_slots = []
    for r, c in self.empty_slots:
      new_board.empty_slots.append((r, c))
    return new_board

  def slot_candidates(self, row: int, column: int) -> SlotCandidates:
    """Returns a integer that represents all possible candidates."""
    return SlotCandidates(self.row[row], self.column[column],
                          self.block[((row // 3) * 3) + (column // 3)])

  @property
  def is_legal(self) -> bool:
    for gp in (self.row + self.column + self.block):
      if not gp.is_legal:
        return False
    return True

  @property
  def is_done(self) -> bool:
    for row in self.row:
      if row.combine != FULL_MASK:
        return False
    return True

  def simple_fill(self) -> SolverResults:
    """Fills all trivial empty slots."""
    is_updated = SolverResults.NO_UPDATE
    self.empty_slots.sort(key=lambda slot: len(self.slot_candidates(*slot)),
                          reverse=True)
    for _ in range(len(self.empty_slots)):
      r, c = self.empty_slots.pop(-1)
      candidate = self.slot_candidates(r, c)
      candidate_count = len(candidate)
      if candidate_count > 1:
        self.empty_slots.append((r, c))
        break
      elif candidate_count == 1:
        is_updated = SolverResults.UPDATE
        self.board[r][c].raw = candidate.raw
      elif candidate_count == 0:
        return SolverResults.CONFLICT
    return is_updated

  def __str__(self) -> str:
    row_list = [
        str(self.row[0]),
        str(self.row[1]),
        str(self.row[2]), '',
        str(self.row[3]),
        str(self.row[4]),
        str(self.row[5]), '',
        str(self.row[6]),
        str(self.row[7]),
        str(self.row[8])
    ]
    return '\n'.join(row_list)

  def __repr__(self) -> str:
    return self.__str__()


def gen_board(user_input: str) -> SudokuBoard:
  """Generate a board from user input string."""
  user_input = user_input.replace(' ', '')
  user_input = user_input.replace('\n', '')
  if len(user_input) != 81:
    raise ValueError('Incomplete Sudoku map.')
  board = []
  for char in user_input:
    try:
      in_num = int(char)
      board.append(in_num)
    except ValueError as e:
      raise ValueError('Invalid character found.') from e
  sudoku_map = SudokuBoard()
  sudoku_map.set_board_num([board[i * 9:i * 9 + 9] for i in range(9)])
  if not sudoku_map.is_legal:
    raise ValueError('Illegal Sudoku configuration.')
  return sudoku_map


def solver(sudoku: SudokuBoard, guess_level: int = 0) -> SolverResults:
  """Solves Sudoku puzzle recursively."""

  # Do simple filling.
  fill_result = SolverResults.UPDATE
  slots_count = len(sudoku.empty_slots)
  while fill_result == SolverResults.UPDATE:
    fill_result = sudoku.simple_fill()

  if fill_result == SolverResults.CONFLICT:
    return fill_result

  slots_count = slots_count - len(sudoku.empty_slots)
  if slots_count:
    print(f'Simple fill solves {slots_count} slots.')

  if sudoku.is_done:
    return SolverResults.ALL_DONE

  # When simple fill can't make any progress.
  r, c = sudoku.empty_slots.pop(-1)
  candidates_pool = sudoku.slot_candidates(r, c)
  for candidate in candidates_pool:
    sudoku_guess = sudoku.clone()
    sudoku_guess.board[r][c].raw = candidate
    print(f'Guess level[{guess_level + 1}]: '
          f'Trying {sudoku_guess.board[r][c]} at ({r}, {c}), '
          f'{len(sudoku_guess.empty_slots)} empty slots left.')
    fill_result = solver(sudoku_guess, guess_level + 1)
    if fill_result == SolverResults.ALL_DONE:
      sudoku.sync_to(sudoku_guess)
      return SolverResults.ALL_DONE
  return fill_result


if __name__ == '__main__':
  if len(sys.argv) <= 1:
    raise ValueError('One needs to specify a puzzle.')
  b = gen_board(sys.argv[1])
  print('Your input puzzle is:')
  print(b)
  print(f'Solver says: {solver(b).name}')
  print('Final state:')
  print(b)
  print('Checker says:',
        'Answer is leagal' if b.is_legal else 'Answer is wrong.')
