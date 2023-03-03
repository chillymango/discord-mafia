import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.kill import Alert
from engine.role.base import RoleGroup
from engine.role.base import TargetGroup
from engine.role.town import TownRole


class Veteran(TownRole):
    """
    Veteran chooses nights to go on alert. They kill all visitors.
    """

    default_ability_uses = 3

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A paranoid, retired admiral who will shoot anyone who bothers him."

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
        return "May go on alert during the night. If he goes on alert, " + \
               "will automatically kills any player who targets him that night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [Alert]

    @property
    def target_group(self) -> TargetGroup:
        """
        Vet is a self-target to activate.
        """
        return TargetGroup.SELF

    @property
    def allow_self_target(self) -> bool:
        return True

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_POWER, RoleGroup.TOWN_KILLING]
