import typing as T

from engine.action.court import Court
from engine.role.base import ActionSequence
from engine.role.base import RoleGroup
from engine.role.base import TargetGroup
from engine.role.neutral import NeutralRole
from engine.wincon import WinCondition
from engine.wincon import EvilWin


class Judge(NeutralRole):

    default_ability_uses = 1

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return EvilWin

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A corrupt court minister who uses his power and connections to manipulate the trials."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "May call court during the day, stopping all discussion and " + \
            "forcing an anonymous ballot vote where the Judge has additional votes."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "You are able to speak as the Crier at night. This allows you to " + \
            "speak to the town anonymously."

    @classmethod
    def day_actions(cls) -> ActionSequence:
        return [Court]

    @property
    def target_group(self) -> TargetGroup:
        return TargetGroup.SELF

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.NEUTRAL_EVIL]
