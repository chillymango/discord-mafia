import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.kill import BodyguardKill
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Citizen(TownRole):
    """
    This role sucks. It's almost a punishment.

    Citizens break ties
    """

    # this role sucks
    DISABLED = True

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_GOVERNMENT]
