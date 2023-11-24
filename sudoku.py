import enum
from typing import Sequence, Self


R_TO_NUM = {0: 0, 1: 1, 2: 2, 4: 3, 8: 4, 16: 5, 32: 6, 64: 7, 128: 8, 256: 9}
FULL_MASK = 0x1FF


class SolverResults(enum.Enum):
  """Solver outcomes."""
  NO_UPDATE = 0
  UPDATE = 1
  CONFLICT = 2
  ALL_DONE = 3


class NumSlot():
  """Representation of a slot in sudoku."""

  def __init__(self, number: int = 0) -> None:
    self.set(number)

  def set(self, number: int):
    """Fills a number to the slot."""
    self.r = 1 << (number - 1) if number else 0

  @property
  def is_fill(self) -> int:
    """Checks if the slot is filled."""
    return int(self.r != 0)

  def __int__(self) -> int:
    return R_TO_NUM[self.r]

  def __str__(self) -> str:
    return str(int(self))

  def __repr__(self) -> str:
    return str(self)


class SlotGroup():
  """Representation of a group of slots."""

  def __init__(self, s1: NumSlot, s2: NumSlot, s3: NumSlot,
               s4: NumSlot, s5: NumSlot, s6: NumSlot,
               s7: NumSlot, s8: NumSlot, s9: NumSlot) -> None:
    self.s1: NumSlot = s1
    self.s2: NumSlot = s2
    self.s3: NumSlot = s3
    self.s4: NumSlot = s4
    self.s5: NumSlot = s5
    self.s6: NumSlot = s6
    self.s7: NumSlot = s7
    self.s8: NumSlot = s8
    self.s9: NumSlot = s9

  @property
  def combine(self) -> int:
    return (self.s1.r | self.s2.r | self.s3.r |
            self.s4.r | self.s5.r | self.s6.r |
            self.s7.r | self.s8.r | self.s9.r)

  @property
  def vacancy(self) -> int:
    return FULL_MASK - self.combine

  @property
  def is_legal(self) -> bool:
    return self.combine.bit_count() == (
      self.s1.is_fill + self.s2.is_fill + self.s3.is_fill +
      self.s4.is_fill + self.s5.is_fill + self.s6.is_fill +
      self.s7.is_fill + self.s8.is_fill + self.s9.is_fill
    )

  def __str__(self) -> str:
    return (f"{self.s1}{self.s2}{self.s3} "
            f"{self.s4}{self.s5}{self.s6} "
            f"{self.s7}{self.s8}{self.s9}")

  def __repr__(self) -> str:
    return str(self)


class SudokuBoard():
  """Representation of one Sudoku board."""

  def __init__(self) -> None:
    """Books a new RAM space for holding the Sudoku puzzle."""
    self.board = [[NumSlot() for _ in range(9)] for __ in range(9)]
    self.row = [SlotGroup(*self.board[i]) for i in range(9)]
    self.column = [SlotGroup(*[r[i] for r in self.board]) for i in range(9)]
    self.block: Sequence[SlotGroup] = []
    for i in [0, 3, 6]:
      for r in [0, 3, 6]:
        self.block.append(
          SlotGroup(*self.board[i][r:r+3],
                    *self.board[i + 1][r:r+3],
                    *self.board[i + 2][r:r+3]))
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
    self.empty_slots = []
    for r, (rowslot, row) in enumerate(zip(self.board, ref.board)):
      for c, (slot, num) in enumerate(zip(rowslot, row)):
        if num == 0:
          self.empty_slots.append((r, c))
        slot.r = num.r

  def clone(self) -> Self:
    """Generates a clone of this board."""
    new_board = SudokuBoard()
    for rowslot, row in zip(new_board.board, self.board):
      for slot, num in zip(rowslot, row):
        slot.r = num.r
    new_board.empty_slots = []
    for r, c in self.empty_slots:
      new_board.empty_slots.append((r, c))
    return new_board

  def slot_candidates(self, row: int, column: int) -> int:
    """Returns a integer that represents all possible candidates."""
    return (self.row[row].vacancy &
            self.column[column].vacancy &
            self.block[((row // 3) * 3) + (column // 3)].vacancy)

  @property
  def is_legal(self) -> bool:
    for gp in (self.row + self.column + self.block):
      if not gp.islegal:
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
    self.empty_slots.sort(
      key=lambda slot: self.slot_candidates(*slot).bit_count(), reverse=True)
    for _ in range(len(self.empty_slots)):
      r, c = self.empty_slots.pop(-1)
      candidate = self.slot_candidates(r, c)
      candidate_count = candidate.bit_count()
      if candidate_count > 1:
        self.empty_slots.append((r, c))
        break
      elif candidate_count == 1:
        is_updated = SolverResults.UPDATE
        self.board[r][c].r = candidate
      elif candidate_count == 0:
        return SolverResults.CONFLICT
    return is_updated

  def __str__(self) -> str:
    row_list = [
      str(self.row[0]), str(self.row[1]), str(self.row[2]), '',
      str(self.row[3]), str(self.row[4]), str(self.row[5]), '',
      str(self.row[6]), str(self.row[7]), str(self.row[8])]
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
    except ValueError:
      raise ValueError('Invalid character found.')
  sudoku_map = SudokuBoard()
  sudoku_map.set_board_num([board[i * 9: i * 9 + 9] for i in range(9)])
  if not sudoku_map.is_legal:
    raise ValueError('Illegal Sudoku configuration.')
  return sudoku_map


def solver(sudoku: SudokuBoard, guess_level: int = 0) -> SolverResults:
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
  candidates = sudoku.slot_candidates(r, c)
  for i in range(9):
    mask = 1 << i
    if mask & candidates:
      sudoku_guess = sudoku.clone()
      sudoku_guess.board[r][c].r = mask
      print(f'Guess level[{guess_level + 1}]: '
            f'Trying {sudoku_guess.board[r][c]} at ({r}, {c}), '
            f'{len(sudoku_guess.empty_slots)} empty slots left.')
      fill_result = solver(sudoku_guess, guess_level + 1)
      if fill_result == SolverResults.ALL_DONE:
        sudoku.sync_to(sudoku_guess)
        return SolverResults.ALL_DONE
  return fill_result



b = gen_board(
  """
800 000 000
003 600 000
070 090 200

050 007 000
000 045 700
000 100 030

001 000 068
008 500 010
090 000 400
  """
)
print('Your input puzzle is:')
print(b)
print(f'Solver says: {solver(b).name}')
print('Final state:')
print(b)
print('Checker says:',
      'Answer is leagal' if b.is_legal else 'Answer is wrong.')
