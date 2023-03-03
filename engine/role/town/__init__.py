import typing as T

from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.role.base import RoleGroup
from engine.affiliation import TOWN


class TownRole(Role):

    @property
    def affiliation(self) -> str:
        return TOWN

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_RANDOM]
