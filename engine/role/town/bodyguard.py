import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.protect import Protect
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Bodyguard(TownRole):
    """
    Bodyguard protects somebody at night. If they are attacked, the bodyguard will
    fight them off. The assailant and the bodyguard will die in the process.
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A war veteran who secretly makes a living by selling protection."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "Your role does not have a day action."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "Guard one player each night. If someone attacks a guarded player, " + \
               "both the attacker and the Bodyguard die instead of the guarded player."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [Protect]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_PROTECTIVE, RoleGroup.TOWN_KILLING]
