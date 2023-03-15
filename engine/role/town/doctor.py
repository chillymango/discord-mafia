import typing as T
from engine.action.base import ActionSequence
from engine.action.heal import Heal
from engine.action.heal import HealReport
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Doctor(TownRole):

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A secret surgeon skilled in trauma care."

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
        return "Visit someone at night to save them if someone tries to kill them."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [Heal, HealReport]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_PROTECTIVE]

    def _role_specific_config_init(self) -> None:
        self._knows_if_target_is_attacked = self._config.role_config.doctor.know_if_target_is_attacked
