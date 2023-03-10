import typing as T

from engine.role.base import Role
from engine.role.base import RoleGroup
from engine.affiliation import NEUTRAL


class NeutralRole(Role):

    @classmethod
    def affiliation(self) -> str:
        return NEUTRAL

    @classmethod
    def groups(cls) -> T.Iterable["RoleGroup"]:
        return super().groups() + [RoleGroup.NEUTRAL_RANDOM]
