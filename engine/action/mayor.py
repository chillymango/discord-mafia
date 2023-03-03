import typing as T

from engine.action.reveal import Reveal

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Mayor(Reveal):
    """
    Reveal and change vote count
    """

    def action_result(self, actor: "Actor", *targets: "Actor") -> T.Optional[bool]:
        """
        Giv vots
        """
        if actor.game.tribunal.mayor_action(actor):
            return True
