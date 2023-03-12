import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.kill import BodyguardKill
from engine.role.base import RoleGroup
from engine.role.neutral import NeutralRole
from engine.wincon import EvilWin
from engine.wincon import WinCondition


class Scumbag(NeutralRole):
    """
    This role sucks. It's literally a punishment.
    """

    # this role cannot be dealt
    DISABLED = True

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return EvilWin

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return []
