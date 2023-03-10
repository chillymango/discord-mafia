import typing as T

from engine.action.base import Action
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Court(Action):
    """
    Move everybody into court chat (how are we gonna do that lol)
    Change vote counts for judge
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
        if actor.game.tribunal.judge_action(actor):
            if not actor.game.town_hall.call_court():
                print(f"Warning: TownHall failed to call court? Def need to fix")
            return True
