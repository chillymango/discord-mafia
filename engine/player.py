"""
Interface to game player (from actor).

This should be 1:1 player:actor but we will keep them separate for now.
"""

class Player:
    """
    Hello there!
    """

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name
