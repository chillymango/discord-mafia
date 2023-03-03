import typing as T

from engine.role.base import RoleGroup
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
        return "	The leader of the town militia."

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
        return "May reveal themselves during the day and allow " + \
               "multiple lynches to occur on the same day."

    @classmethod
    def unique(cls) -> bool:
        return True

    @classmethod
    def dayactions(cls) -> T.List["Action"]:
        return [MarshallAction]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_GOVERNMENT]
