from enum import StrEnum


class MasteryState(StrEnum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    FRAGILE = "FRAGILE"
    RETAINED = "RETAINED"
    MASTERED = "MASTERED"
    NEEDS_RELEARNING = "NEEDS_RELEARNING"
    ARCHIVED = "ARCHIVED"


class Difficulty(StrEnum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"
