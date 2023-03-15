import typing as T

from engine.action.audit import Audit
from engine.action.base import ActionSequence
from engine.role.neutral import NeutralRole
from engine.wincon import WinCondition
from engine.wincon import EvilWin


class Auditor(NeutralRole):

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A corrupt government tax agent who uses his knowledge and connections for evil."

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return EvilWin

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
        return "Convert one person to Citizen each night. Mafia instead " \
            "become a Mafioso; Triad instead becomes an Enforcer. Neutrals " \
            "become a Scumbag.\n\n" \
            "* You cannot audit anyone who is Night Immune.\n" \
            "* You cannot audit members of the Cult.\n" \
            "* You cannot audit anyone who is being protected by a Bodyguard.\n"

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [Audit]

    def _role_specific_config_init(self) -> None:
        self._ability_uses = self._config.role_config.auditor.number_of_audits
