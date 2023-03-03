import typing as T

from engine.action.reveal import Reveal

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Marshall(Reveal):
    """
    Group lynch
    """

    def action_result(self, actor: "Actor", *targets: "Actor") -> T.Optional[bool]:
        """
        Modify the Tribunal for the day.
        """
        if actor.game.tribunal.marshall_action():
            return True
