import typing as T

from engine.action.base import Action

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Court(Action):
    """
    Move everybody into court chat (how are we gonna do that lol)
    Change vote counts for judge
    """

    def action_result(self, actor: "Actor", *targets: "Actor") -> T.Optional[bool]:
        """
        Modify the Tribunal for the day.
        """
        if actor.game.tribunal.judge_action(actor):
            return True
