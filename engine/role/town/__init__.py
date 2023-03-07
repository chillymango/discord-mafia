import typing as T

from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.role.base import RoleGroup
from engine.affiliation import TOWN
from engine.wincon import WinCondition
from engine.wincon import TownWin


class TownRole(Role):

    @classmethod
    def affiliation(self) -> str:
        return TOWN

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return TownWin

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_RANDOM]
