from engine.role.base import Role
from engine.affiliation import NEUTRAL


class NeutralRole(Role):

    @property
    def affiliation(self) -> str:
        return NEUTRAL
