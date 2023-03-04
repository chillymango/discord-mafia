import typing as T

from engine.role.base import RoleGroup
from engine.role.town import TownRole
from engine.action.kill import ConstableKill

if T.TYPE_CHECKING:
    from engine.action.base import Action


class Constable(TownRole):
    """
    The Constable just shoots somebody
    """

    default_ability_uses = 1

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A grizzled lawman who's nearly at his breaking point with the Town situation."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "Choose someone to shoot during the day. They will instantly die."

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
        return [ConstableKill]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_GOVERNMENT]
