"""
Role Base Class
"""
from enum import Enum
import typing as T

from engine.action.base import ActionSequence
from engine.action.base import TargetGroup

from proto import state_pb2


class Role:
    """
    Base Role Object (BRO)
    """

    DISABLED = False

    default_ability_uses: int = -1
    default_vests: int = 0
    default_night_immune: bool = False
    default_rb_immune: bool = False
    default_intercept_rb: bool = False
    default_target_immune: bool = False
    default_detect_immune: bool = False
    default_cannot_be_healed: bool = False

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "TODO: fill out role description."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "Your role does not have a day action."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "Your role does not have a night action."

    @classmethod
    def unique(cls) -> bool:
        """
        Roles by default are not unique.

        During game setup, more than one unique role will not be allowed to join the game.
        """
        return False

    @property
    def name(self) -> str:
        # translate it from camel case if needed
        if self._name is not None:
            return self._name

        name = ""
        for prev_char, next_char in zip(self.__class__.__name__[:-1], self.__class__.__name__[1:]):
            name += prev_char
            if prev_char == prev_char.lower() and next_char == next_char.upper():
                name += " "

        name += next_char
        self._name = name

        return name

    def __repr__(self) -> str:
        return self.name

    def __init__(self, config: T.Dict[str, T.Any]) -> None:
        """
        We will look for a config section specifically for our role.
        A subsection of the large game config should be passed in here.

        If we do not find one, we will use a default config.
        The default config should also be defined in this class.
        """
        self._name = None
        self._config = config
        self._init_with_config()

    def _init_with_config(self) -> None:
        """
        Write in some basic role stats from config.

        Classes with more interesting behavior should generally call this super method additionally
        """
        # Ability Uses
        # typically we do ability counts per action sequence, so if there's
        # a multiple sequence interaction, doing both should consume one charge
        self._ability_uses = self._config.get("ability_uses", self.default_ability_uses)  # using -1 means infinite uses

        self._allow_self_target = self._config.get("allow_self_target", False)

        # Common Immunities
        self._night_immune = self._config.get("night_immune", self.default_night_immune)
        self._rb_immune = self._config.get("roleblock_immune", self.default_rb_immune)
        self._intercept_rb = self._config.get("intercept_rb", self.default_intercept_rb)
        self._target_immune = self._config.get("target_immune", self.default_target_immune)
        self._detect_immune = self._config.get("detect_immune", self.default_detect_immune)
        self._cannot_be_healed = self._config.get("cannot_be_healed", self.default_cannot_be_healed)

        self._vests = self._config.get("vests", self.default_vests)

    def to_proto(self) -> state_pb2.Role:
        role = state_pb2.Role(name=self.name)
        role.role_description = self.role_description()
        if self.day_actions():
            role.action_description = self.day_action_description()
        elif self.night_actions():
            role.action_description = self.night_action_description()
        else:
            role.action_description = "You have no possible actions."
        role.affiliation = self.affiliation
        return role

    @property
    def vests(self) -> int:
        return self._vests

    def use_vest(self) -> bool:
        if self._vests > 0:
            return True
        return False

    def consume_vest(self) -> None:
        self._vests -= 1

    def give_vest(self) -> None:
        self._vests += 1

    @property
    def target_group(self) -> TargetGroup:
        """
        Most actions will target live players.
        """
        return TargetGroup.LIVE_PLAYERS

    @property
    def allow_self_target(self) -> bool:
        return self._allow_self_target

    @property
    def affiliation(self) -> str:
        return ""

    @classmethod
    def groups(cls) -> T.Iterable["RoleGroup"]:
        return [RoleGroup.ANY_RANDOM]

    @classmethod
    def day_actions(cls) -> ActionSequence:
        return []

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return []

    def _check_target_count_consistency(self, actions: ActionSequence):
        target_count = None
        for action in actions:
            if target_count is None:
                target_count = action.targets
            if target_count != action.targets:
                return False
        return True

    def validate(self) -> bool:
        """
        General check is to make sure that all actions have the same number of targets
        """
        return (
            self._check_target_count_consistency(self.day_actions())
            and self._check_target_count_consistency(self.night_actions())
        )


class RoleGroup(Enum):
    """
    Role Groups for setup flexibility
    """

    # CATCHALL
    ANY_RANDOM = "AnyRandom"

    # TOWN ROLES
    TOWN_GOVERNMENT = "TownGovernment"
    TOWN_SUPPORT = "TownSupport"
    TOWN_INVESTIGATIVE = "TownInvestigative"
    TOWN_KILLING = "TownKilling"
    TOWN_POWER = "TownPower"
    TOWN_PROTECTIVE = "TownProtective"
    TOWN_RANDOM = "TownRandom"

    # MAFIA ROLES
    MAFIA_KILLING = "MafiaKilling"
    MAFIA_SUPPORT = "MafiaSupport"
    MAFIA_DECEPTION = "MafiaDeception"
    MAFIA_RANDOM = "MafiaRandom"

    # TRIAD ROLES
    TRIAD_KILLING = "TriadKilling"
    TRIAD_SUPPORT = "TriadSupport"
    TRIAD_DECEPTION = "TriadDeception"
    TRIAD_RANDOM = "TriadRandom"

    # NEUTRAL ROLES
    NEUTRAL_KILLING = "NeutralKilling"
    NEUTRAL_EVIL = "NeutralEvil"
    NEUTRAL_BENIGN = "NeutralBenign"
    NEUTRAL_RANDOM = "NeutralRandom"


class RoleFactory:

    def __init__(self, config: T.Dict[str, T.Any]) -> None:
        self._config = config

    def create_role(self, role: T.Type["Role"] = None) -> "Role":
        role_name = role.__name__
        role_config = self._config.get(role_name, {})
        if role_config is None:
            print(f"WARNING: no config found for role {role_name}")
        return role(role_config)

    def create_by_name(self, role_name: str) -> T.Optional["Role"]:
        # TODO: shitty pattern, fix circ import
        from engine.role import NAME_TO_ROLE
        role = NAME_TO_ROLE.get(role_name)
        if role is None:
            return None
        return self.create_role(role)
