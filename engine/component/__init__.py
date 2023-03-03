import typing as T

from engine.phase import TurnPhase

if T.TYPE_CHECKING:
    from engine.game import Game


class Component:
    """
    This is a base class for an object that performs some sort of state
    change whenever the game loop changes.

    It's kinda like a MonoBehaviour in Unity.

    I guess we can hardcode game phases? And then for each one we just run them
    in the same order each time.
    """

    @classmethod
    def enabled_in_phases(cls) -> T.List[TurnPhase]:
        """
        Components by default are active in all phases
        """
        return list(TurnPhase)

    def __init__(self, game: "Game", *args, **kwargs) -> None:
        self._game = game
        self._args = args
        self._kwargs = kwargs

    @property
    def enabled(self) -> bool:
        """
        This should generally work, where the component specifies in what turn phases it's enabled.

        Subclasses can override this as desired.
        """
        if self._game.turn_phase in self.enabled_in_phases:
            return True
        return False

    async def drive(self) -> None:
        """
        Child classes should call this I guess.
        """
