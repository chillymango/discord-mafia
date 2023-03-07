import typing as T

from engine.action.base import Action

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Obscure(Action):
    """
    Prevent somebody's role and last will from being released on their death.
    """

    def action_result(self, actor: "Actor", *targets: "Actor") -> T.Optional[bool]:
        return super().action_result(actor, *targets)
