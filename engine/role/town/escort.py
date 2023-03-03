import typing as T
from engine.action.base import ActionSequence
from engine.action.roleblock import Roleblock
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Escort(TownRole):

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A scantily-clad escort, working in secret."

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
        return "Block someone's role at night, canceling their night abilities."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [Roleblock]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_SUPPORT]
