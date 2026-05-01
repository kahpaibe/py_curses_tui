"""
Base color palette definition
"""

from abc import ABC
from dataclasses import dataclass
from typing import TypeAlias

# =====================================
#  Color numbers
# =====================================


@dataclass
class TerminalColor:
    """RGB color for the terminal"""

    r: int  # [0-1000]
    g: int  # [0-1000]
    b: int  # [0-1000]


TerminalColors: TypeAlias = list[TerminalColor]  # Index is the terminal color number.

TERMINAL_COLORS_BW: TerminalColors = [
    TerminalColor(0, 0, 0),  # 0 -> black
    TerminalColor(1000, 1000, 1000),  # 1 -> white
]

TERMINAL_COLORS_BASIC: TerminalColors = [
    TerminalColor(0, 0, 0),  # 0 -> black
    TerminalColor(1000, 0, 0),  # 1 -> red
    TerminalColor(0, 1000, 0),  # 2 -> green
    TerminalColor(1000, 1000, 0),  # 3 -> yellow
    TerminalColor(0, 0, 1000),  # 4 -> blue
    TerminalColor(1000, 0, 1000),  # 5 -> magenta
    TerminalColor(0, 1000, 1000),  # 6 -> cyan
    TerminalColor(1000, 1000, 1000),  # 7 -> white
]

# =====================================
#  Color pairs
# =====================================

ColorPairs: TypeAlias = list[
    tuple[int, int]
]  # Index (starting from 1) is color pair number

COLOR_PAIRS_BW: ColorPairs = [
    (7, 0),  # 1 -> White on Black
]

COLOR_PAIRS_BASIC: ColorPairs = [
    (7, 0),  # 1 -> White on Black
    (1, 0),  # 2 -> Red on Black
    (2, 0),  # 3 -> Green on Black
    (3, 0),  # 4 -> Yellow on Black
    (4, 0),  # 5 -> Blue on Black
    (5, 0),  # 6 -> Magenta on Black
    (6, 0),  # 7 -> Cyan on Black
    (0, 7),  # 8 -> Black on White
    (1, 7),  # 9 -> Red on White
    (2, 7),  # 10 -> Green on White
    (3, 7),  # 11 -> Yellow on White
    (4, 7),  # 12 -> Blue on White
    (5, 7),  # 13 -> Magenta on White
    (6, 7),  # 14 -> Cyan on White
]

# =====================================
#  Palette
# =====================================


@dataclass
class Palette(ABC):
    """Base color palette definition. Values are algebraic color pairs."""

    primary: int
    secondary: int
    tertiary: int


PALETTE_BW: Palette = Palette(
    primary=1,
    secondary=-1,
    tertiary=-1,
)

PALETTE_BASIC: Palette = Palette(
    primary=1,
    secondary=2,
    tertiary=3,
)


# =====================================
#  Set attributes and color pairs
# =====================================
