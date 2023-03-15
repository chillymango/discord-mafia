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

    def _role_specific_config_init(self) -> None:
        self._ability_uses = self._config.role_config.party_host.number_of_parties
