import typing as T

from engine.action.base import Action

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Armor(Action):
    """
    Give somebody a bulletproof vest
    """

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        # if this got called we should still have charges left
        target.role.give_vest()
        return True

    def target_text_success(self) -> str:
        return "You gave your target a bulletproof vest."

    def feedback_text_success(self) -> str:
        return "Someone gave you a bulletproof vest."
