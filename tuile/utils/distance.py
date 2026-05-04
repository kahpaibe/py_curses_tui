"""
Distance between drawables definition.
"""

from enum import Enum


class Direction(Enum):
    """Navigation direction."""

    DOWN = 0
    RIGHT = 1
    UP = 2
    LEFT = 3


def _distance_down(y1: int, x1: int, y2: int, x2: int, max_lim: int) -> int:
    """Order described (example 6x6 with max_lim = 6):
    147 150 153 101 104 107
    148 151 154 102 105 108
    149 152 155 103 106 109
     50  53   1   4   7  10
     51  54   2   5   8  11
     52  55   3   6   9  12
    """
    dx, dy = x2 - x1, y2 - y1

    if dy > 0 and dx >= 0:  # zone 1, bottom right
        sup = 0  # supplement value to get in which zone we are
        return sup + dy + dx * (max_lim - y1 - 2)
    elif dy > 0:  # and dx < 0 # zone 2, bottom left
        sup = max_lim * max_lim
        return sup + dy + x2 * (max_lim - y1 - 2)
    elif dx > 0:  # and dy <= 0 # zone 3, top right
        sup = 2 * max_lim * max_lim
        return sup + y2 + (y1 + 1) * dx
    else:  # dy <= 0 and dx <= 0 # zone 4, top left
        sup = 3 * max_lim * max_lim
        return sup + y2 + (y1 + 1) * x2


def _distance_right(y1: int, x1: int, y2: int, x2: int, max_lim: int) -> int:
    """Order described (example 6x6 with max_lim = 6):
    144 150 156  37  38  39
    145 151 157   1   2   3
    146 152 109  73  76  79
    147 153 110  74  77  80
    148 154 111  75  78  81
    149 155 112  76  79  82
    """
    dx, dy = x2 - x1, y2 - y1

    if dy == 0 and dx > 0:  # zone 1, right
        sup = 0  # supplement value to get in which zone we are
        return sup + dx
    elif dy < 0 and dx > 0:  # zone 2, top right
        sup = max_lim * max_lim
        return sup + y1 - y2 + y1 * (dx - 1)
    elif dy > 0 and dx > 0:  # zone 3, bottom right
        sup = 2 * max_lim * max_lim
        return sup + dy + (dx - 1) * (max_lim - y1 - 2)
    elif dy > 0 and dx == 0:  # zone 4, just below
        sup = 3 * max_lim * max_lim
        return sup + dy
    else:  # dx <= 0 or (dx == 0 and dy <= 0) # zone 5, top left
        sup = 4 * max_lim * max_lim
        return sup + y2 + x2 * max_lim


def _distance_up(y1: int, x1: int, y2: int, x2: int, max_lim: int) -> int:
    """Order described (example 6x6 with max_lim = 6):
      6   4   2  40  42  44
      5   3   1  39  41  43
     74  73 172 171 170 169
    128 127 166 165 164 163
    122 121 160 159 158 157
    116 115 154 153 152 151
    """
    dx, dy = x2 - x1, y2 - y1

    if dy < 0 and dx <= 0:  # zone 1, top left
        sup = 0  # supplement value to get in which zone we are
        return sup + y1 - y2 + y1 * (-dx)
    elif dy < 0 and dx > 0:  # zone 2, top right
        sup = max_lim * max_lim
        return sup + y1 - y2 + y1 * dx
    elif dy == 0 and dx < 0: # zone 3, left
        sup = 2 * max_lim * max_lim
        return sup + x1 - x2
    elif dy > 0 and dx < 0:  # zone 4, bottom left
        sup = 3 * max_lim * max_lim
        return sup + x1 - x2 + max_lim * (max_lim - y2)
    else:  # dy >= 0 and dx >= 0 # zone 5, bottom right
        sup = 4 * max_lim * max_lim
        return sup + max_lim - x2 + (max_lim - y2) * max_lim


def _distance_left(y1: int, x1: int, y2: int, x2: int, max_lim: int) -> int:
    """Order described (example 6x6 with max_lim = 6):
    40  38 168 162 156 150
    39  37 169 163 157 151
     2   1 170 164 158 152
    79  73 109 165 159 153
    80  74 110 166 160 154
    81  75 111 167 161 155
    """
    dx, dy = x2 - x1, y2 - y1

    if dy == 0 and dx < 0:  # zone 1, left
        sup = 0  # supplement value to get in which zone we are
        return sup + (-dx)
    elif dy < 0 and dx < 0:  # zone 2, top left
        sup = max_lim * max_lim
        return sup + y1 - y2 + y1 * (-dx - 1)
    elif dy > 0 and dx < 0:  # zone 3, bottom left
        sup = 2 * max_lim * max_lim
        return sup + dy + (-dx - 1) * max_lim
    elif dy > 0 and dx == 0:  # zone 4, just below
        sup = 3 * max_lim * max_lim
        return sup + dy
    else: # dy <= 0 and dx >= 0 # zone 5, top right
        sup = 4 * max_lim * max_lim
        return sup + y2 + (max_lim - x2) * max_lim

def distance(
    origin_y: int,
    origin_x: int,
    target_y: int,
    target_x: int,
    direction: Direction,
    rows: int,
    cols: int,
) -> int:
    """Distance between two points."""
    MAX_DELTA = max(rows, cols)

    y1, x1 = origin_y, origin_x
    y2, x2 = target_y, target_x
    if direction == Direction.DOWN:
        return _distance_down(y1, x1, y2, x2, MAX_DELTA)
    elif direction == Direction.RIGHT:
        return _distance_right(y1, x1, y2, x2, MAX_DELTA)
    elif direction == Direction.UP:
        return _distance_up(y1, x1, y2, x2, MAX_DELTA)
    elif direction == Direction.LEFT:
        return _distance_left(y1, x1, y2, x2, MAX_DELTA)
    else:
        raise ValueError(f"Invalid direction: {direction}")


if __name__ == "__main__":
    # Make 3D plot of the distance function for a fixed origin and direction.
    import numpy as np

    rows, cols = 6, 6
    origin_y, origin_x = 2, 2

    for direction in Direction:
        # Show np array of distances in the grid
        distances = np.zeros((rows, cols), dtype=int)
        for y in range(rows):
            for x in range(cols):
                distances[y, x] = distance(origin_y, origin_x, y, x, direction, rows, cols)
        print(f"Distances for direction {direction.name}:\n{distances}\n")
