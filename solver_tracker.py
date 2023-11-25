"""Tracker for recording."""


class SolverTracker():
  """Tracking sudoku solver steps."""

  def __init__(self, init_slots: int, mute: bool = False) -> None:
    self.slot_count: list[int] = [init_slots]
    self.guess_lv: list[int] = [0]
    self.mute = mute

  def log_guess(self, slot_count: int, guess_lv: int, guess_num: int,
                guess_pos: tuple[int, int]) -> None:
    self.slot_count.append(slot_count)
    self.guess_lv.append(guess_lv)
    if not self.mute:
      print(f'Guess level[{guess_lv}]: Trying {guess_num} at {guess_pos}, '
            f'{slot_count} empty slots left.')

  def log_simple_fill(self, slot_count: int) -> None:
    change = self.slot_count[-1] - slot_count
    if change > 0:
      self.slot_count.append(slot_count)
      self.guess_lv.append(self.guess_lv[-1])
      if not self.mute:
        print(f'Simple fill solves {change} slots.')

  @property
  def total_steps(self) -> int:
    return len(self.slot_count)

  def ascii_plot(self, height: int = 17, width: int = 100) -> str:
    if self.total_steps > width:
      group_size = -(self.total_steps // -width)
      slot_count = []
      guess_lv = []
      for i in range(self.total_steps // group_size):
        slot_count.append(
            round(
                sum(self.slot_count[i * group_size:(i + 1) * group_size]) /
                group_size))
        guess_lv.append(
            round(
                sum(self.guess_lv[i * group_size:(i + 1) * group_size]) /
                group_size))
    else:
      slot_count = self.slot_count
      guess_lv = self.guess_lv
    scaler_1 = min(height / (max(slot_count) + 1), 1)
    scaler_2 = min(height / (max(guess_lv) + 1), 1)

    max_1 = max(*slot_count, height - 1)
    l1_max = f'{max_1:02}'
    l1_mid = f'{round(max_1 / 2):02}'
    max_2 = max(*guess_lv, height - 1)
    l2_max = f'{max_2:02}'
    l2_mid = f'{round(max_2 / 2):02}'

    l_s = round((height - 3) / 2)

    buffer = [
        f'0{" " * l_s}{l1_mid[0]}{" " * (height - 3 - l_s)}{l1_max[0]}',
        f'0{"┊" * l_s}{l1_mid[1]}{"┊" * (height - 3 - l_s)}{l1_max[1]}'
    ]
    for a, b in zip(slot_count, guess_lv):
      a = int(a * scaler_1)
      b = int(b * scaler_2)
      if a == b:
        buffer.append(f'{"┊" * a}◈{" " * (height - a - 1)}')
      elif a > b:
        buffer.append(f'{"┊" * b}◇{"┊" * (a - b - 1)}◆{" "*(height - a - 1)}')
      else:
        buffer.append(f'{"┊" * a}◆{" " * (b - a - 1)}◇{" "*(height - b - 1)}')
    buffer.append(
        f'0{"┊" * l_s}{l2_mid[0]}{"┊" * (height - 3 - l_s)}{l2_max[0]}')
    buffer.append(
        f'0{" " * l_s}{l2_mid[1]}{" " * (height - 3 - l_s)}{l2_max[1]}')
    width = len(buffer) // 2
    t_buffer: list[str] = [
        f'Slots◆ ┄┄{"┄" * (width - 9)}┄{"┄" * (width - 12)}┄┄Guess_lvl◇'
    ]
    for i in range(height - 1, -1, -1):
      t_buffer.append(''.join([c[i] for c in buffer]))
    return '\n'.join(t_buffer)
