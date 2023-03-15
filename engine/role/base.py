"""
Role Base Class
"""
from collections import defaultdict
from collections import deque
from enum import Enum
import logging
import typing as T

from engine.action.base import ActionSequence
from engine.action.base import TargetGroup

from engine.affiliation import MAFIA
from engine.affiliation import NEUTRAL
from engine.affiliation import TOWN
from engine.affiliation import TRIAD
from engine.wincon import AutoVictory
from engine.wincon import WinCondition
import log
from proto import state_pb2
from util.string import camel_to_snake

if T.TYPE_CHECKING:
    from engine.config import GameConfig
    from engine.game import Game

logger = logging.getLogger(__name__)
logger.addHandler(log.ch)
logger.setLevel(logging.INFO)


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
    def affiliation_description(cls) -> str:
        """
        This should describe the role's affiliation.
        """
        if cls.affiliation() == TOWN:
            return "You are a member of the Town. You do not know who your teammates are. You " + \
                "must exercise caution, strategy, and teamwork to survive."

        if cls.affiliation() == MAFIA:
            return "You are a member of the Mafia. A member of an organized crime family, you " + \
                "should know who your teammates are. You must work together in secrecy to " + \
                "eliminate all your opposition and come to rule this town."

        if cls.affiliation() == TRIAD:
            return "You are a member of the Triad. A member of an organized crime family, you " + \
                "should know who your teammates are. You must work together in secrecy to " + \
                "eliminate all your opposition and come to rule this town."

        if cls.affiliation() == NEUTRAL:
            return "You are a Neutral character. You are not affiliated with the Town, the Triad, " + \
                "or the Mafia. You have your own specific win condition."

        return "Your affiliation is unknown. Please contact the game developers."

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return AutoVictory

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

    @classmethod
    def name_repr(cls) -> str:
        # TODO: replace `.name` with this
        name = ""
        for prev_char, next_char in zip(cls.__name__[:-1], cls.__name__[1:]):
            name += prev_char
            if prev_char == prev_char.lower() and next_char == next_char.upper():
                name += " "
        name += next_char
        return name

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

    def __init__(self, config: "GameConfig") -> None:
        """
        We will look for a config section specifically for our role.
        A subsection of the large game config should be passed in here.

        If we do not find one, we will use a default config.
        The default config should also be defined in this class.
        """
        self._name = None
        self._config = config
        self._init_with_config()

    def init_with_game(self, game: "Game") -> None:
        """
        Given a game, initialize the role.

        This is called for classes to setup after the game has started.
        Example uses would be for classes like the Executioner, where they
        will need to setup the class with some attributes.

        By default this method will not do anything.
        """

    def _init_with_config(self) -> None:
        """
        Write in some basic role stats from config.

        Classes with more interesting behavior should generally call this super method additionally.

        This will set default values per class. The `role_specific_config_init` method should be used
        to follow up with config overrides.
        """
        # Ability Uses
        # typically we do ability counts per action sequence, so if there's
        # a multiple sequence interaction, doing both should consume one charge
        self._ability_uses = -1

        # Bulletproof Vests
        self._vests = 0

        # Common Immunities
        self._night_immune = False
        self._rb_immune = False
        self._intercept_rb = False
        self._target_immune = False  # TODO: implement
        self._detect_immune = False
        self._cannot_be_healed = False

        self._allow_self_target = False

        self._role_specific_config_init()

    def _role_specific_config_init(self) -> None:
        """
        Inheriting classes define this
        """

    def to_proto(self) -> state_pb2.Role:
        role = state_pb2.Role(name=self.name)
        role.role_description = self.role_description()
        if self.day_actions():
            role.action_description = self.day_action_description()
        elif self.night_actions():
            role.action_description = self.night_action_description()
        else:
            role.action_description = "You have no possible actions."
        role.affiliation = self.affiliation()
        role.ability_uses = self._ability_uses
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
        return self._allow_self_target or self.target_group == TargetGroup.SELF

    @classmethod
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

    @classmethod
    def create_from_name(cls, name: str) -> "RoleGroup":
        """
        Do some name formatting

        Tries the following in order:
            * build from value directly
            * build from name directly
            * infer from value
        """
        out = None
        try:
            out = cls(name)
        except (KeyError, ValueError):
            pass

        if out is not None:
            return out
        
        try:
            out = cls[name]
        except (KeyError, ValueError):
            pass

        if out is not None:
            return out
        
        try:
            munged = name.replace(' ', '')
            out = cls(munged)
        except (KeyError, ValueError):
            pass
        
        if out is not None:
            return out
        
        raise ValueError(f"Could not create RoleGroup enum from {name}")


class RoleGroupNode:

    def __init__(self, group: T.Union["RoleGroup", "Role"]) -> None:
        self._group: T.Union["RoleGroup", "Role"] = group
        self._children: T.List["RoleGroupNode"] = []

    def __repr__(self) -> str:
        return f"Node - {self._group.name}"

    @property
    def is_role(self) -> bool:
        return isinstance(self._group, Role)

    @property
    def is_group(self) -> bool:
        return isinstance(self._group, RoleGroup)

    @property
    def is_leaf(self) -> bool:
        return not any([isinstance(child, RoleGroupNode) for child in self._children])

    def add_child_node(self, node: "RoleGroupNode") -> None:
        self._children.append(node)

    def add_child_group(self, group: "RoleGroup") -> "RoleGroupNode":
        """
        Create a node for the group
        """
        node = RoleGroupNode(group)
        self.add_child_node(node)
        return node

    def add_child_roles(self) -> None:
        """
        If we're storing a role group, add all roles as children.
        If we're storing a role, don't do anything
        """
        if self.is_group:
            self._children.extend(get_group_map().get(self._group, []))


def get_group_map() -> T.Dict["RoleGroup", T.List["Role"]]:
    global GROUP_MAP
    if GROUP_MAP is not None:
        return GROUP_MAP

    from engine.role import ALL_ROLES
    mapping = defaultdict(list)
    for role in ALL_ROLES:
        for group in role.groups():
            if not role.DISABLED:
                mapping[group].append(role)

    # do not return a defaultdict
    GROUP_MAP = {key: value for key, value in mapping.items()}
    return GROUP_MAP


GROUP_MAP = None


def construct_role_tree() -> RoleGroupNode:
    """
    Create the standard role group tree and return the root node
    """

    root = RoleGroupNode(RoleGroup.ANY_RANDOM)
    town = root.add_child_group(RoleGroup.TOWN_RANDOM)
    mafia = root.add_child_group(RoleGroup.MAFIA_RANDOM)
    neutral = root.add_child_group(RoleGroup.NEUTRAL_RANDOM)

    # town subgroups
    town.add_child_group(RoleGroup.TOWN_GOVERNMENT)
    town.add_child_group(RoleGroup.TOWN_INVESTIGATIVE)
    town.add_child_group(RoleGroup.TOWN_KILLING)
    town.add_child_group(RoleGroup.TOWN_POWER)
    town.add_child_group(RoleGroup.TOWN_PROTECTIVE)
    town.add_child_group(RoleGroup.TOWN_SUPPORT)

    # mafia subgroups
    mafia.add_child_group(RoleGroup.MAFIA_DECEPTION)
    mafia.add_child_group(RoleGroup.MAFIA_KILLING)
    mafia.add_child_group(RoleGroup.MAFIA_SUPPORT)

    # neutral subgroups
    neutral.add_child_group(RoleGroup.NEUTRAL_BENIGN)
    neutral.add_child_group(RoleGroup.NEUTRAL_EVIL)
    neutral.add_child_group(RoleGroup.NEUTRAL_KILLING)

    # traverse all nodes and if leaf node, populate with roles as children
    to_visit: T.List[RoleGroupNode] = [root]
    while to_visit:
        node = to_visit.pop()
        if not isinstance(node, RoleGroupNode):
            raise ValueError(f"Invalid node {node}")

        if node.is_leaf:
            node.add_child_roles()
        else:
            to_visit.extend([child for child in node._children])

    return root


def role_group_tree(root: "RoleGroupNode" = None) -> T.List[T.Union["RoleGroup", "Role"]]:
    """
    Returns a list of nodes that traverses the role group tree in order. The order should
    start from the bottom of the tree and work its way to the top of the tree.
    """
    root = root or construct_role_tree()
    to_visit = deque([root])
    output_order = deque()
    while to_visit:
        node = to_visit.popleft()
        if node is None:
            continue

        to_visit.extend([child for child in node._children
                         if isinstance(child, RoleGroupNode)
                         and isinstance(child._group, RoleGroup)])

        output_order.appendleft(node._group)
    return output_order


def construct_role_group_tree_map() -> T.Dict[RoleGroup, RoleGroupNode]:
    """
    Construct a role group tree and then return the node corresponding
    to the specified role group
    """
    tree_map = dict()
    to_visit = [construct_role_tree()]
    while to_visit:
        node = to_visit.pop()
        tree_map[node._group] = node
        for child in node._children:
            if isinstance(child, RoleGroupNode):
                to_visit.append(child)
    return tree_map


class RoleFactory:

    def __init__(self, config:"GameConfig") -> None:
        self._config = config

    def create_role(self, role: T.Type["Role"]) -> "Role":
        return role(self._config)

    def create_by_name(self, role_name: str) -> T.Optional["Role"]:
        # TODO: shitty pattern, fix circ import
        from engine.role import NAME_TO_ROLE
        role = NAME_TO_ROLE.get(role_name)
        if role is None:
            return None
        return self.create_role(role)
