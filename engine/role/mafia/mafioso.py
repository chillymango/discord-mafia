import typing as T
from engine.action.kill import MafiaKill
from engine.role.base import RoleGroup
from engine.role.mafia import MafiaRole


class Mafioso(MafiaRole):
    """
    Kills somebody every night
    """

    # do not allow spawn by default
    DISABLED = True

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A lowly soldato for one of the Don's borgata."

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
        return "Choose one player to kill each night."

    @classmethod
    def unique(cls) -> bool:
        return True

    @classmethod
    def night_actions(cls):
        return [MafiaKill]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_KILLING]
