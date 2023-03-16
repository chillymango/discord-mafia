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
        vote_count = actor.game._config.role_config.judge.vote_count
        if actor.game.tribunal.judge_action(actor, votes=vote_count):
            if not actor.game.town_hall.call_court():
                actor.game.log.warning("TownHall failed to call court")
            return True
