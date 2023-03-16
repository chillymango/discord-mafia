import typing as T

from engine.action.reveal import Reveal
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Marshall(Reveal):
    """
    Group lynch
    """

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.CORRUPTION],
        }

    @classmethod
    def instant(cls) -> bool:
        return True

    def action_result(self, actor: "Actor", *targets: "Actor") -> T.Optional[bool]:
        """
        Modify the Tribunal for the day.
        """
        if actor.game.tribunal.marshall_action():
            return True
