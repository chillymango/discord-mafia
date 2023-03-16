import typing as T

from engine.role.base import RoleGroup
from engine.role.base import TargetGroup
from engine.role.town import TownRole
from engine.action.marshall import Marshall as MarshallAction

if T.TYPE_CHECKING:
    from engine.action.base import Action


class Marshall(TownRole):
    """
    Mayor reveals and changes the number of lynches allowed in a day
    """

    default_ability_uses = 1

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "The leader of the town militia."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "During the day, you may activate your ability to initiate a group lynch. Multiple " \
            "executions may happen on that day. If someone gets enough votes to go to trial, they " \
            "will instead be immediately lynched."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "Your role does not have a night action."

    @classmethod
    def unique(cls) -> bool:
        return True

    @classmethod
    def day_actions(cls) -> T.List["Action"]:
        return [MarshallAction]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_GOVERNMENT]

    @property
    def target_group(self) -> TargetGroup:
        """
        Most actions will target live players.
        """
        return TargetGroup.SELF

    def _role_specific_config_init(self) -> None:
        self._group_executions_allowed = self._config.role_config.marshall.group_executions_allowed
        self._executions_per_group = self._config.role_config.marshall.executions_per_group
        self._cannot_be_healed = self._config.role_config.marshall.cannot_be_healed
