import typing as T

from engine.action.base import ActionSequence
from engine.action.base import TargetGroup
from engine.action.lookout import Lookout as ALookout
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Lookout(TownRole):
    """
    Watches peoples houses
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "An eagle-eyed observer, stealthily camping outside houses to gain information."

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
        return "See everyone who visits your target each night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [ALookout]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_INVESTIGATIVE]
