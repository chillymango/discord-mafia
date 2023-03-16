import typing as T

from engine.action.base import Action
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Obscure(Action):
    """
    Prevent somebody's role and last will from being released on their death.
    """

    # run this soon after kills are processed
    ORDER = 150

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.DESTRUCTION_OF_PROPERTY],
        }

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        if not target.is_alive:
            target._visible_role = None
            target._last_will = None  # None means LW was obscured, empty string means empty LW
            return True
        # do not deduct ability usage if obscuring did not succeeed
        return None
