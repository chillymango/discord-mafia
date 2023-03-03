import typing as T

from engine.action.base import Action
from engine.crimes import Crime
from engine.affiliation import MAFIA
from engine.affiliation import TOWN
from engine.affiliation import TRIAD

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Heal(Action):
    """
    If somebody gets killed, bring them back to life.

    Cannot target people who are already dead.
    """

    # apply these before kill orders so if their HP dips to zero or below we pop them
    ORDER = 80

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        if not target.cannot_be_healed:
            target.hitpoints += 1
            return True
        return False


class HealReport(Action):
    """
    Look at your target after combat has passed.

    TODO: how do you check to see if your target was attacked
    """

    ORDER = 110

    def feedback_text_success(self) -> str:
        return "Your target was attacked! You were able to tend to their wounds."

    def target_text_success(self) -> str:
        return "You were attacked and left for dead, but an unknown stranger nursed you back to health!"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        """
        Look at the target. If they were attacked, report it to the healer.
        Do not report to the Healer if the target was eventually overwhelmed by attacks.
        """
        if target.was_attacked and target.is_alive:
            return True
        return False
