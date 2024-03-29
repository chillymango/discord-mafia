import typing as T

from engine.action.base import ActionSequence
from engine.role.base import RoleGroup
from engine.role.neutral import NeutralRole
from engine.wincon import WinCondition
from engine.wincon import SurvivorWin


class Survivor(NeutralRole):

    default_vests = 4

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return SurvivorWin

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "An apathetic individual who just wants to stay alive."

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
        return "Your role does not have a night action."

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.NEUTRAL_BENIGN]

    def _role_specific_config_init(self) -> None:
        self._vests = self._config.role_config.survivor.number_of_bulletproof_vests
