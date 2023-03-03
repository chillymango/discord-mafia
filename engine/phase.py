from enum import Enum


class GamePhase(Enum):
    """
    Game Phase Descriptor
    """
    INITIALIZING = 0
    IN_PROGRESS = 1
    CONCLUDED = 2


class TurnPhase(Enum):
    """
    Turn Phases
    """
    INITIALIZING = 0
    DAYBREAK = 1
    DAYLIGHT = 2
    DUSK = 3
    NIGHT = 4
    NIGHT_SEQUENCE = 5
