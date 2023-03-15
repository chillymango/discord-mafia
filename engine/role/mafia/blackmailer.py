import typing as T
from engine.action.silence import Silence
from engine.role.base import RoleGroup
from engine.role.mafia import MafiaRole


class Blackmailer(MafiaRole):
    """
    Prevent somebody from speaking during the next day.
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A manipulative eavesdropper who uses information to shut people up."

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
        return "Silence your target, preventing them from speaking during the next day and night."

    @classmethod
    def night_actions(cls):
        return [Silence]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_SUPPORT]

    def _role_specific_config_init(self) -> None:
        self._victim_can_speak_during_trial = self._config.role_config.blackmailer.blackmailed_person_can_talk_during_trial
