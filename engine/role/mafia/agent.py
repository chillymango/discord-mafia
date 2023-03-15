import typing as T
from engine.action.follow import Follow
from engine.action.lookout import Lookout
from engine.role.base import RoleGroup
from engine.role.mafia import MafiaRole


class Agent(MafiaRole):
    """
    Shadow somebody to see who visited them and who they visited
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "One of the many Caporegime the Don employs, this shady " + \
               "individual gathers information for the Mafia."

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
        return "See who one person visits and is visited by each night."

    @classmethod
    def night_actions(cls):
        return [Follow, Lookout]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_SUPPORT]

    def _role_specific_config_init(self) -> None:
        self._nights_between_shadowings = self._config.role_config.agent.nights_between_shadowings
