import typing as T

from engine.action.base import Action

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Annoy(Action):
    """
    An insane person visited you
    """

    def action_result(self, actor: "Actor", *targets: "Actor") -> None:
        """
        This should succeed always

        TODO: what about street racer?
        """
        return True

    def target_text_success(self) -> str:
        return "You visited your target tonight."

    def feedback_text_success(self) -> str:
        return "An insane person visited you tonight."
