from engine.action.base import Action


class Swap(Action):
    """
    Switch the position of two players at night, causing actions that target
    one to target another.
    """

    ORDER = 20
