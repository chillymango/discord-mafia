from engine.action.investigate import InvestigateExact
from engine.role.mafia import MafiaRole


class Consigliere(MafiaRole):
    """
    Get somebody's exact role every night
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A counselor to the boss of a crime family."

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
        return "Investigate one player to get their exact role each night."

    @classmethod
    def unique(cls) -> bool:
        return True

    @classmethod
    def night_actions(cls):
        return [InvestigateExact]

    def _role_specific_config_init(self) -> None:
        self._detects_exact_role = self._config.role_config.consigliere.detects_exact_role
