import typing as T
from engine.action.frame import Frame
from engine.role.base import RoleGroup
from engine.role.mafia import MafiaRole


class Beguiler(MafiaRole):
    """
    Hide behind somebody each night.
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A skilled forger working for organized crime."

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
        return "Frame one player each night, giving them a random " + \
               "crime, and make them appear evil to investigators."

    def _init_with_config(self) -> None:
        super()._init_with_config()
        self._can_hide_behind_team = self._config.get("can_hide_behind_team", True)

    @classmethod
    def night_actions(cls):
        return [Frame]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_DECEPTION]
