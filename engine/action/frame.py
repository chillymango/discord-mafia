import random
import typing as T

from engine.action.base import Action
from engine.crimes import Crime
from engine.role.mafia.agent import Agent
from engine.role.mafia.beguiler import Beguiler
from engine.role.mafia.blackmailer import Blackmailer
from engine.role.mafia.consigliere import Consigliere
from engine.role.mafia.consort import Consort
# don't import Framer, it's circular -- and make it so we can't Frame someone that
# way anyways LOL
from engine.role.mafia.janitor import Janitor
from engine.role.mafia.mafioso import Mafioso
from engine.role.neutral.auditor import Auditor
from engine.role.neutral.judge import Judge
from engine.role.neutral.serialkiller import SerialKiller
from engine.role.neutral.massmurderer import MassMurderer

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Frame(Action):
    """
    Add a random crime and evil alignment to target player.

    The crime and alignment are random and do not necessarily match.
    """

    # run this before any investigative checks
    ORDER = 250

    def feedback_text_success(self) -> str:
        role = self._action_result.get("framed_role", "UNKNOWN")
        crime = self._action_result.get("framed_crime", "UNKNOWN")
        return f"You framed your target as a {role} with the crime of {crime}"

    def feedback_text_fail(self) -> str:
        return "You were unable to Frame your target."

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        """
        Action succeeds unless actor has been killed or is visit immune

        TODO: implement visit immunity
        """
        if not target.is_alive:
            # do not deduct an ability use
            return None

        evil_roles = (
            Agent,
            Auditor,
            Beguiler,
            Blackmailer,
            Consigliere,
            Consort,
            Janitor,
            Judge,
            Mafioso,
            SerialKiller,
            MassMurderer
        )

        chosen_evil = random.choice(evil_roles)
        target.set_investigated_role(chosen_evil)

        chosen_crime = random.choice(list(Crime))

        self._action_result["framed_role"] = chosen_evil.__name__
        self._action_result["framed_crime"] = chosen_crime.value

        return True
