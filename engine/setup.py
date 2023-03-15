"""
Game Setup

The config should call out the setup.
"""
import asyncio
from collections import defaultdict
from collections import deque
from contextlib import contextmanager
import logging
import numpy as np
import random
import typing as T

from aiogoogle.auth.creds import ServiceAccountCreds

from engine.actor import Actor
from engine.config import GameConfig
from engine.role import NAME_TO_ROLE
from engine.role.base import construct_role_group_tree_map
from engine.role.base import role_group_tree
from engine.role.base import get_group_map
from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.role.base import RoleGroup
from engine.role.base import RoleGroupNode
from engine.role.mafia.godfather import Godfather
from engine.role.neutral.jester import Jester
from engine.role.town.doctor import Doctor
from engine.role.town.investigator import Investigator
from engine.role.town.escort import Escort
from engine.stepper import sleep_override
from engine.tribunal import Tribunal
from util.string import camel_to_english
import log

if T.TYPE_CHECKING:
    from engine.game import Game
    from engine.role.base import RoleGroupNode

logger = logging.getLogger(__name__)
logger.addHandler(log.ch)
logger.setLevel(logging.INFO)


# do not give bots advanced roles
BOT_BLOCKLIST = [
    "Jailor",
    "Kidnapper",
    "Mayor",
    "Constable",
    "Marshall",
    "Judge",
]


EXAMPLE_CONFIG = {
    "roles": {
        "Godfather": {
            "night_immune": True,
            "rb_immune": True,
            "target_immune": False,
            "detect_immune": True,
        },
        "Lookout": {
            "allow_self_target": True,
        },
        "SerialKiller": {
            "intercept_rb": True,
            "rb_immune": True,
            "night_immune": True,
            "detect_immune": True,
        }
    },
    "turns": {
        # these are minimum lengths, if there are lots of things to print, we'll go longer
        "phase_lengths": {
            "daybreak": 10.0,
            "daylight": 20.0,
            "dusk": 10.0,
            "night": 20.0,
            "night_sequence": 5.0,
        }
    },
    "setup": {
        # assume we'll have 15 players (fill with bots if needed)
        "role_list": [
            "RoleGroup::TownGovernment",
            "RoleGroup::TownInvestigative",
            "RoleGroup::TownProtective",
            "RoleGroup::TownKilling",
            "RoleGroup::TownPower",
            "RoleGroup::TownSupport",
            "RoleGroup::TownRandom",
            "RoleGroup::TownRandom",
            "RoleName::Godfather",
            "RoleGroup::MafiaRandom",
            "RoleGroup::MafiaRandom",
            "RoleName::SerialKiller",
            "RoleName::Jester",
            "RoleName::Survivor",
            "RoleGroup::AnyRandom",
            #"RoleGroup::AnyRandom",
            #"RoleGroup::AnyRandom",
        ],
        # scalings for odds in RoleGroup selections
        # if the role is not listed, it's assumed to be 0
        "role_weights": {}
    }
}

DEFAULT_CONFIG = GameConfig.default_with_role_list([
    "Town Government",
    "Town Protective",
    "Town Investigative",
    "Town Power",
    "Town Killing",
    "Town Support",
    "Town Random",
    "Town Random",
    "Godfather",
    "Mafia Random",
    "Mafia Random",
    "Neutral Killing",
    "Neutral Random",
    "Neutral Random",
    "Any Random",
])


class WeightedSampler:
    """
    Initialize with setup role weights

    Supports sampling from different categories.
    """

    def __init__(
        self,
        role_weights: T.Dict[str, float],
        excludes_list: T.List[T.Tuple[str, str]],
    ) -> None:
        self._role_weights = role_weights
        self._excludes_list = excludes_list
        self._group_map = get_group_map()

        self._build_excludes_map()

    def _build_excludes_map(self) -> None:
        self._excludes_map: T.Dict[RoleGroup, T.List[Role]] = defaultdict(list)
        role_group_tree_map = construct_role_group_tree_map()
        for excluding, excluded in self._excludes_list:
            try:
                group = RoleGroup.create_from_name(excluded)
                excluded_roles: T.List[Role] = list()
                root = role_group_tree_map[group]
                to_visit = [root]
                while to_visit:
                    node = to_visit.pop()
                    for child in node._children:
                        if isinstance(child, type):  # TODO: sloppy
                            excluded_roles.append(child)
                        elif isinstance(child, RoleGroupNode):
                            to_visit.append(child)
                        else:
                            raise ValueError(f"Unknown {node}")
                self._excludes_map[RoleGroup.create_from_name(excluding)].extend(excluded_roles)
                continue
            except:
                pass

            role = NAME_TO_ROLE.get(excluded)
            if role is None:
                raise ValueError(f"Unknown role {excluded}")
            self._excludes_map[excluding].append(role)

    @classmethod
    def create_from_config(cls, config: "GameConfig") -> "WeightedSampler":
        return cls(
            role_weights=config.role_weights,
            excludes_list=config.excludes_list,
        )

    @contextmanager
    def temp_weights(self, **weights: T.Dict[str, T.Any]) -> T.Iterator[None]:
        """
        TODO: this is probably slower than it needs to be
        """
        orig = self._role_weights.copy()
        try:
            self._role_weights.update(weights)
            yield
        finally:
            self._role_weights = orig.copy()

    def sample_from_group(self, role_group: "RoleGroup") -> T.Optional[T.Type["Role"]]:
        try:
            valid_roles = self._group_map.get(role_group)
            for role in self._excludes_map[role_group]:
                if role in valid_roles:
                    valid_roles.remove(role)
            if not valid_roles:
                return None

            weight_vec = np.array([self._role_weights.get(r, 0.3) for r in valid_roles])
            weight_vec = weight_vec / sum(weight_vec)
            return np.random.choice(
                valid_roles,
                1,
                replace=False,
                p=weight_vec
            )[0]
        except IndexError:
            # select first option
            return valid_roles[0]


def do_setup(game: "Game", config: "GameConfig" = DEFAULT_CONFIG, override_player_count: bool = False, skip: bool = False) -> T.Tuple[bool, str]:
    """
    If setup succeeds, return True
    Otherwise return False

    Also includes any output string, primarily used to indicate what went wrong
    """
    if game.get_actors():
        return False, "Game is already setup"

    if not config.role_list:
        return False, "Missing setup config"

    role_list: T.List[str] = config.role_list[:]
    if not override_player_count and (len(game.players) != len(role_list)):
        return False, f"Mismatched number of players. Have {len(game.players)} and need {len(role_list)}"

    sampler = WeightedSampler.create_from_config(config)
    rf = RoleFactory(config)

    selected_roles: T.List[T.Type[Role]] = list()
    node_order = dict([(camel_to_english(node.value), idx)
                       for idx, node in enumerate(role_group_tree())])

    # order our role_list by the node_order
    role_list.sort(key=lambda x: node_order.get(x, -1))

    for role_spec_name in role_list:
        # try to make an exact role first
        if role_spec_name in NAME_TO_ROLE:
            selected_roles.append(NAME_TO_ROLE[role_spec_name])
            continue

        tries = 0
        while tries < 3:
            tries += 1
            group = RoleGroup.create_from_name(role_spec_name)
            sampled = sampler.sample_from_group(group)
            if sampled is None:
                return False, f"Could not sample from {group}"
            
            # vague preference in role assignments to avoid multiple
            # copies of the same role but not forced
            if sampled not in selected_roles:
                selected_roles.append(sampled)
                break
        else:
            # use the last one
            selected_roles.append(sampled)

    if len(selected_roles) != len(game._players):
        return False, f"Did not generate a full list of roles for the game"

    # map out which actors can be selected for which roles
    # people are eligible for every role except the ones they have on blocklist
    eligible_players: T.Dict[Role, T.List[Player]] = dict()
    for role in selected_roles:
        eligible_players[role] = game._players[:]

    for player in game._players:
        if player in config.blocked_role:
            blocked_role = NAME_TO_ROLE[config.blocked_role[player]]
            eligible_players[blocked_role].remove(player)

        if player in config.preferred_role:
            preferred_role = NAME_TO_ROLE[config.preferred_role[player]]
            eligible_players[preferred_role].extend([player] * 2)

    # go from smallest group size to largest
    ordered_roles = selected_roles[:]
    ordered_roles.sort(key=lambda x: len(eligible_players.get(x, [])))
    ordered_players: T.List[Player] = list()
    for role in ordered_roles:
        chosen_player = random.choice(eligible_players[role])

        for remaining_players in eligible_players.values():
            while chosen_player in remaining_players:
                remaining_players.remove(chosen_player)

        ordered_players.append(chosen_player)

    game.add_actors(*[Actor(player, rf.create_role(role), game) for player, role in zip(ordered_players, ordered_roles)])
    random.shuffle(game._actors)
    game.tribunal = Tribunal(game)

    for actor in game.actors:
        actor.role.init_with_game(game)
    return True, "Successfully setup the game"


if __name__ == "__main__":
    import json
    import random
    from engine.config import SheetsFetcher
    from engine.game import Game
    from engine.player import Player
    with open('service_token.json') as service_token:
        token = json.loads(service_token.read())

    creds = ServiceAccountCreds(**token)
    fetch = SheetsFetcher(creds)
    SHEET_ID = '1PMiXU_B2eATCXlZuFsEuKFa9KjDCSWdC9ONlQ6OZY6Q'

    async def main() -> None:
        config = await GameConfig.parse_from_google_sheets_id(SHEET_ID)
        print('done?')
        game = Game(config)
        game.add_players(*[Player(f"Player-{random.randint(100, 999)}") for _ in range(15)])
        success, msg = do_setup(game, config)
        print(game.actors)

    asyncio.run(main())
