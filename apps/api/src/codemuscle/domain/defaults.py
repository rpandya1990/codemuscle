from collections.abc import Mapping
from typing import Final

from codemuscle.domain.enums import Difficulty

DEFAULT_SUCCESS_INTERVALS: Final[tuple[int, ...]] = (3, 10, 30, 90, 180, 365)

DEFAULT_PROBLEM_DURATION_MINUTES: Final[Mapping[Difficulty, int]] = {
    Difficulty.EASY: 15,
    Difficulty.MEDIUM: 25,
    Difficulty.HARD: 30,
    Difficulty.UNKNOWN: 20,
}
