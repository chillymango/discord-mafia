import typing as T

from engine.action.base import ActionSequence
from engine.action.kill import SerialKillerKill
from engine.action.nou import NoU
from engine.role.base import RoleGroup
from engine.role.neutral import NeutralRole
from engine.wincon import WinCondition
from engine.wincon import SerialKillerWin


class SerialKiller(NeutralRole):

    default_night_immune = True
    default_rb_immune = True
    default_intercept_rb = True

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return SerialKillerWin

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A deranged criminal who hates the world."

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
        return "Choose one target to kill each night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [SerialKillerKill]

    @classmethod
    def groups(cls) -> T.Iterable["RoleGroup"]:
        return super().groups() + [RoleGroup.NEUTRAL_KILLING, RoleGroup.NEUTRAL_EVIL]

    def _role_specific_config_init(self) -> None:
        self._night_immune = self._config.role_config.serial_killer.invulnerable_at_night
        self._rb_immune = self._config.role_config.serial_killer.kills_role_blockers
        self._intercept_rb = self._config.role_config.serial_killer.kills_role_blockers
        self._detect_immune = self._config.role_config.serial_killer.immune_to_detection
