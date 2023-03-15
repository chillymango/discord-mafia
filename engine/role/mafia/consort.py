from engine.action.roleblock import Roleblock
from engine.role.mafia import MafiaRole


class Consort(MafiaRole):
    """
    Roleblock someone every night
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A dancer working for organized crime."

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
        return "Roleblock one player each night."

    @classmethod
    def night_actions(cls):
        return [Roleblock]

    def _role_specific_config_init(self) -> None:
        self._rb_immune = self._config.role_config.consort.cannot_be_roleblocked
        self._detect_block_immune = self._config.role_config.consort.detects_block_immune_target
