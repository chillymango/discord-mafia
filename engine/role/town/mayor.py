import typing as T

from engine.action.mayor import Mayor as MayorAction
from engine.role.base import TargetGroup
from engine.role.base import RoleGroup
from engine.role.town import TownRole

if T.TYPE_CHECKING:
    from engine.action.base import Action


class Mayor(TownRole):
    """
    Mayor reveals and gains extra votes
    """

    default_ability_uses = 1

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "The governor of the Town. The Mayor can confirm themselves as Mayor " + \
               "and can act as an organizing force to lead the Town to victory."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "May reveal themselves during the day and thereafter have additional votes."

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
        return [MayorAction]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_GOVERNMENT]

    @property
    def target_group(self) -> TargetGroup:
        """
        Most actions will target live players.
        """
        return TargetGroup.SELF

