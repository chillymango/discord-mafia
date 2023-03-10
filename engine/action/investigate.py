import typing as T

from engine.action.base import Action
from engine.crimes import Crime
from engine.affiliation import MAFIA
from engine.affiliation import TOWN
from engine.affiliation import TRIAD

if T.TYPE_CHECKING:
    from engine.actor import Actor


class InvestigateCrimes(Action):
    """
    Discover crime record of target
    """

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable[Crime]]:
        return {True: [Crime.TRESPASSING], False: [Crime.TRESPASSING]}

    def feedback_text_success(self) -> str:
        crimes = self._action_result.get("crimes")
        if not crimes:
            return "You have determined that your target has not committed any crimes."
        return f"Your target has committed: {', '.join(crimes)}"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Tuple[bool, str]:
        """
        Look at the target and return its crime list.
        """
        print(f"Investigate crimes {actor.name} -> {target.name}")
        self._action_result["crimes"] = [crime.value.capitalize() for crime in target.investigated_crimes]
        return True


class InvestigateSuspicion(Action):
    """
    Discover affiliation of target (generally grouped)
    """

    def feedback_text_success(self) -> str:
        suspicion = self._action_result.get("suspicion", "UNKNOWN [BUG]")
        if suspicion == "Not Suspicious":
            return "Your target is not suspicious"
        if suspicion in (MAFIA, TRIAD):
            return f"Your target is a member of the {suspicion.capitalize()}!"
        return f"Your target is a {suspicion.capitalize()}!"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Tuple[bool, str]:
        """
        Look at target and return warnings for some affiliations
        """
        self.reset_results()
        self._action_result["suspicion"] = target.investigated_suspicion
        return True


class InvestigateExact(Action):
    """
    Discover exact role of target
    """

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable[Crime]]:
        return {True: [Crime.TRESPASSING], False: [Crime.TRESPASSING]}

    def feedback_text_success(self) -> str:
        return f"Your target is a {self._action_result['role']}"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Tuple[bool, str]:
        """
        Determine the exact role of a target. This does not bypass detection immunity by
        default.
        """
        self.reset_results()
        self._action_result["role"] = target.investigated_role
        return True
