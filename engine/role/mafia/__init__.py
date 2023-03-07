import typing as T

from engine.role.base import Role
from engine.role.base import RoleGroup
from engine.role.base import TargetGroup
from engine.affiliation import MAFIA
from engine.wincon import WinCondition
from engine.wincon import MafiaWin


class MafiaRole(Role):

    @classmethod
    def affiliation(self) -> str:
        return MAFIA

    @property
    def target_group(self) -> TargetGroup:
        return TargetGroup.LIVING_NON_MAFIA

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return MafiaWin

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.MAFIA_RANDOM]
