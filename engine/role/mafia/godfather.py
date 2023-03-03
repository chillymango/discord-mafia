import typing as T
from engine.action.kill import MafiaKill
from engine.role.base import RoleGroup
from engine.role.mafia import MafiaRole


class Godfather(MafiaRole):
    """
    Kills somebody every night
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "The capofamiglia of the town's organized mafia syndicate. Use your " + \
               "powerful defenses and leadership to lead the Mafia to victory."

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
        return "Kill one player each night."

    default_night_immune = True
    default_rb_immune = True
    default_detect_immune = True

    @classmethod
    def unique(cls) -> bool:
        return True

    @classmethod
    def night_actions(cls):
        return [MafiaKill]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_KILLING]
