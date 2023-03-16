import typing as T

from engine.action.reveal import Reveal
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Mayor(Reveal):
    """
    Reveal and change vote count
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
        Giv vots
        """
        if actor.game.tribunal.mayor_action(actor, votes=actor.game._config.role_config.mayor.vote_count):
            return True
