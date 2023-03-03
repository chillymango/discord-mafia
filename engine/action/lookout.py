import typing as T

from engine.action.base import Action
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Lookout(Action):
    """
    Discover everybody who visited your target
    """

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.TRESPASSING],
            False: [Crime.TRESPASSING],
        }

    def feedback_text_success(self) -> str:
        visitors = self._action_result.get("visitors", [])
        if not visitors:
            return "Your target did not receive any visitors"
        return f"Your target was visited by: {', '.join(visitors)}"

    def feedback_text_fail(self) -> str:
        return "Something went wrong. Please contact the developers."

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        """
        Publish a private message to our actor with results.
        """
        self._action_result["visitors"] = [anon.name for anon in actor.game.get_live_actors() if target in anon.targets]
        return True
