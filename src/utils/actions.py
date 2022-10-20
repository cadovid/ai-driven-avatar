from enum import Enum, unique

@unique
class Action(Enum):
    RIGHT = 0
    LEFT = 1
    DOWN = 2
    UP = 3
    EAT = 4
    DRINK = 5
    PICK_UP = 6
    SLEEP = 7
    STAND_STILL = 8
