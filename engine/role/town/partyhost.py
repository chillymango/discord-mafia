import typing as T

from engine.action.base import ActionSequence
from engine.action.party import Party
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class PartyHost(TownRole):

    # useless role until we get chat done
    DISABLED = True

    @classmethod
    def day_actions(cls) -> ActionSequence:
        return [Party]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_SUPPORT]
