import typing as T

from engine.action.base import ActionSequence
from engine.action.kill import MassMurder
from engine.role.base import RoleGroup
from engine.role.neutral import NeutralRole
from engine.wincon import WinCondition
from engine.wincon import MassMurdererWin


class MassMurderer(NeutralRole):

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return MassMurdererWin

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A crazed spree killer who thinks entrail-spilling is an art form."

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
        return "Perform a killing spree at someone's house each night, " + \
               "killing anyone who visits that player at night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [MassMurder]

    @classmethod
    def groups(cls) -> T.Iterable["RoleGroup"]:
        return super().groups() + [RoleGroup.NEUTRAL_KILLING, RoleGroup.NEUTRAL_EVIL]

    def _role_specific_config_init(self) -> None:
        self._night_immune = self._config.role_config.mass_murderer.invulnerable_at_night
        self._detect_immune = self._config.role_config.mass_murderer.immune_to_detection
        self._nights_between_sprees = self._config.role_config.mass_murderer.nights_between_sprees
        self._allow_self_target = self._config.role_config.mass_murderer.can_self_target
