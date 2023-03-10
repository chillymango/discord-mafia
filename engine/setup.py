"""
Game Setup

The config should call out the setup.
"""
import asyncio
from collections import defaultdict
import numpy as np
import random
import typing as T

from engine.role import NAME_TO_ROLE
from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.role.base import RoleGroup
from engine.role.mafia.godfather import Godfather
from engine.role.neutral.jester import Jester
from engine.role.town.doctor import Doctor
from engine.role.town.investigator import Investigator
from engine.role.town.escort import Escort
from engine.stepper import sleep_override
from engine.tribunal import Tribunal

if T.TYPE_CHECKING:
    from engine.game import Game


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
        ],
        # scalings for odds in RoleGroup selections
        # if the role is not listed, it's assumed to be 0
        "role_weights": {
#            # Town Roles
#            "Doctor": 0.3,
#            "Escort": 0.5,
#            "Lookout": 0.2,
#            "Consort": 0.3,
#
#            # Mafia Roles
#            "Godfather": 0.0,
#
#            # Triad Roles
#
#            # Neutral Roles

        }
    }
}


def get_group_map() -> T.Dict["RoleGroup", T.List["Role"]]:
    from engine.role import ALL_ROLES
    mapping = defaultdict(list)
    for role in ALL_ROLES:
        for group in role.groups():
            mapping[group].append(role)

    # do not return a defaultdict
    return {key: value for key, value in mapping.items()}


class WeightedSampler:
    """
    Initialize with setup role weights

    Supports sampling from different categories.
    """

    def __init__(
        self,
        setup_config: T.Dict[str, T.Any],
        group_map: T.Dict["RoleGroup", T.List[T.Type["Role"]]]
    ) -> None:
        self._config = setup_config
        self._group_map = group_map
        self._initialize_weights()

    def _initialize_weights(self) -> None:
        if 'role_weights' not in self._config or not self._config["role_weights"]:
            print("Falling back to even weighting")
            self._weights: T.Dict[T.Type["Role"], float] = defaultdict(lambda: 1.0)
        else:
            # if it's not in role weights, assume we don't want the role at all
            self._weights: T.Dict[T.Type["Role"], float] = defaultdict(lambda: 0.0)
            for role_name, weight in self._config["role_weights"].items():
                role = NAME_TO_ROLE.get(role_name)
                if role is None:
                    print(f"Warning: unknown role {role_name}")
                    continue
                try:
                    self._weights[role] = float(weight)
                except ValueError:
                    print(f"Warning: unknown weight {weight}. Using 0.0")
                    self._weights[role] = 0.0

    def sample_from_group(self, role_group: "RoleGroup") -> T.Optional[T.Type["Role"]]:
        try:
            valid_roles = self._group_map.get(role_group)
            if not valid_roles:
                return None
            weight_vec = np.array([self._weights[r] for r in valid_roles])
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


def do_setup(game: "Game", config: T.Dict[str, T.Any] = EXAMPLE_CONFIG, override_player_count: bool = False, skip: bool = False) -> T.Tuple[bool, str]:
    """
    If setup succeeds, return True
    Otherwise return False

    Also includes any output string, primarily used to indicate what went wrong
    """
    if game.get_actors():
        return False, "Game is already setup"

    # get all known roles
    setup_config: T.Dict = config.get("setup")
    if setup_config is None or setup_config.get("role_list") is None or setup_config.get("role_weights") is None:
        return False, "Malformed config"

    # each role has hardcoded defaults, these can be interpreted as overrides, and not technically necessary
    role_config = config.get("roles", {})

    role_list: T.List[str] = setup_config["role_list"]
    if not override_player_count and (len(game.players) != len(role_list)):
        return False, f"Mismatched number of players. Have {len(game.players)} and need {len(role_list)}"

    required_roles: T.List[str] = []
    flexible_roles: T.List[str] = []
    for role in role_list:
        spec_type, _, spec_name = role.partition('::')
        if spec_type == "RoleGroup":
            flexible_roles.append(spec_name)
        elif spec_type == "RoleName":
            required_roles.append(spec_name)
        else:
            return False, f"Unknown role specification type {spec_type}"

    # process required roles first
    all_roles: T.List[Role] = []
    rf = RoleFactory(config=role_config)
    for required in required_roles:
        role = rf.create_by_name(required)
        if role is None:
            return False, f"Unknown role specification value {required}"
        all_roles.append(role)

    # do the flexible roles
    group_map = get_group_map()

    sampler = WeightedSampler(setup_config, group_map)
    for flexible in flexible_roles:
        # pick a random role out of the ones that match
        try:
            role_group = RoleGroup(flexible)
        except ValueError:
            return False, f"Unknown Role Group {flexible}"

        max_tries = 50
        tries = 0
        while True:
            tries += 1
            if tries > max_tries:
                raise ValueError(f"Failed to assign roles. Something wrong with {role_group.name}")
            try:
                role = sampler.sample_from_group(role_group)
                if role.unique():
                    found = False
                    for existing in all_roles:
                        if isinstance(existing, role):
                            print(f'Skipping unique role {role.name}')
                            found = True
                            break
                    if found:
                        continue

                if role.DISABLED:
                    continue

                all_roles.append(rf.create_role(role))
                break
            except Exception as exc:
                print(repr(exc))
                return False, f"Failed to sample from group {role_group}"
    
    # we have roles and players, do a random assignment 1:1
    random.shuffle(all_roles)
    try:
        game.assign_roles(all_roles)
    except ValueError as err:
        return False, f"Failed to assign roles: {repr(err)}"

    # create Tribunal
    if skip:
        sleep = sleep_override
    else:
        sleep = asyncio.sleep
    game.tribunal = Tribunal(game, config.get("trial", {}))

    return True, "Successfully setup the game"


def test(config = EXAMPLE_CONFIG) -> None:

    # get all known roles
    setup_config = config.get("setup")
    if setup_config is None or setup_config.get("role_list") is None or setup_config.get("role_weights") is None:
        return False, "Malformed config"

    # each role has hardcoded defaults, these can be interpreted as overrides, and not technically necessary
    role_config = config.get("role", {})

    role_list: T.List[str] = setup_config["role_list"]

    required_roles: T.List[str] = []
    flexible_roles: T.List[str] = []
    for role in role_list:
        spec_type, _, spec_name = role.partition('::')
        if spec_type == "RoleGroup":
            flexible_roles.append(spec_name)
        elif spec_type == "RoleName":
            required_roles.append(spec_name)
        else:
            return False, f"Unknown role specification type {spec_type}"

    # process required roles first
    all_roles: T.List[Role] = []
    rf = RoleFactory(config=role_config)
    for required in required_roles:
        role = rf.create_by_name(required)
        if role is None:
            return False, f"Unknown role specification value {required}"
        all_roles.append(role)

    # do the flexible roles
    group_map = get_group_map()

    sampler = WeightedSampler(setup_config, group_map)
    for flexible in flexible_roles:
        # pick a random role out of the ones that match
        try:
            role_group = RoleGroup(flexible)
        except ValueError:
            return False, f"Unknown Role Group {flexible}"

        while True:
            try:
                role = sampler.sample_from_group(role_group)
                if role.unique():
                    found = False
                    for existing in all_roles:
                        if isinstance(existing, role):
                            print(f'Skipping unique role {existing.name}')
                            found = True
                            break
                    if found:
                        continue

                all_roles.append(rf.create_role(role))
                break
            except Exception as exc:
                print(repr(exc))
                return False, f"Failed to sample from group {role_group}"

    return all_roles


if __name__ == "__main__":
    wtf = test()
    print(wtf)
    import IPython; IPython.embed()
