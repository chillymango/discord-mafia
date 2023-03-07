import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.jail import Jail
from engine.action.kill import JailorKill
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Jailor(TownRole):
    """
    Jailor selects somebody to jail during the day.

    At night, they can choose to execute the person.

    Jail action during day should fix target at night.
    """

    # TODO: fix this omg
    DISABLED = True

    @classmethod
    def day_actions(cls) -> ActionSequence:
        return [Jail]

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [JailorKill]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_POWER, RoleGroup.TOWN_KILLING]
