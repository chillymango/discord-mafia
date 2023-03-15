import typing as T
from engine.action.base import ActionSequence
from engine.action.armor import Armor
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Armorsmith(TownRole):

    default_ability_uses = 3

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A master craftsman who produces protective clothing"

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
        return "Visit someone at night to give them a bulletproof vest."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [Armor]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_PROTECTIVE, RoleGroup.TOWN_SUPPORT]

    def _role_specific_config_init(self) -> None:
        self._ability_uses = self._config.role_config.armorsmith.number_of_vests
