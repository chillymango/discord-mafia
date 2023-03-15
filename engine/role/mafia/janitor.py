import typing as T
from engine.action.obscure import Obscure
from engine.role.base import RoleGroup
from engine.role.mafia import MafiaRole


class Janitor(MafiaRole):
    """
    Prevents somebody's role and last will from being revealed each night
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A sanitation expert working for organized crime."

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
        return "Sanitize one player each night, preventing their role and last will " + \
               "from being released upon their death."

    @classmethod
    def night_actions(cls):
        return [Obscure]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_DECEPTION]

    def _role_specific_config_init(self) -> None:
        self._ability_uses = self._config.role_config.janitor.number_of_sanitations
