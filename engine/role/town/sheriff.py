import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.investigate import InvestigateSuspicion
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Sheriff(TownRole):
    """
    Sheriff checks someone's alignment
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A member of law enforcement, forced into hiding because of the threat of murder."

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
        return "Check one player each night for criminal activity."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [InvestigateSuspicion]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_INVESTIGATIVE]

    def _role_specific_config_init(self) -> None:
        self._detects_mafia = self._config.role_config.sheriff.detects_mafia
        self._detects_serial_killer = self._config.role_config.sheriff.detects_serial_killer
        self._detects_mass_murderer = self._config.role_config.sheriff.detects_mass_murderer
