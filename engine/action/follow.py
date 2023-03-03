import typing as T

from engine.action.base import Action
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Follow(Action):
    """
    Discover who your target visited.

    This ignores detection immunity by default.
    """

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.TRESPASSING],
            False: [Crime.TRESPASSING],
        }

    def feedback_text_success(self) -> str:
        visited = self._action_result.get("visited", [])
        if not visited:
            return "Your target did not visit anybody."
        return f"Your target visited: {', '.join(visited)}"

    def feedback_text_fail(self) -> str:
        return "Something went wrong. Please contact the developers."

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        """
        Publish a private message to our actor with results.
        """
        self.reset_results()
        self._action_result["visited"] = [targ.name for targ in target.targets]
        return True
