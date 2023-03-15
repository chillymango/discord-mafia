import typing as T
from engine.action.redirect import Hide
from engine.role.base import RoleGroup
from engine.role.base import TargetGroup
from engine.role.mafia import MafiaRole


class Beguiler(MafiaRole):
    """
    Hide behind somebody each night.
    """

    default_ability_uses = 4

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A stealthy sneak who uses manipulation and redirection to survive. "

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
        return "Hide behind someone each night, causing anyone who targets you to target them instead."

    @property
    def target_group(self) -> TargetGroup:
        return TargetGroup.BEGUILER

    @classmethod
    def night_actions(cls):
        return [Hide]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_DECEPTION]

    def _role_specific_config_init(self) -> None:
        self._can_hide_behind_team = self._config.role_config.beguiler.can_hide_behind_mafia
