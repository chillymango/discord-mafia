import asyncio
import random
import typing as T
from collections import defaultdict
from dataclasses import dataclass

from engine.actor import Actor
from engine.affiliation import MAFIA
from engine.affiliation import TOWN
from engine.affiliation import TRIAD
from engine.report import DeathReporter
from engine.message import Messenger
from engine.phase import GamePhase
from engine.phase import TurnPhase
from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.role.base import RoleGroup
from engine.role.neutral.massmurderer import MassMurderer
from engine.role.neutral.serialkiller import SerialKiller
from proto import state_pb2

if T.TYPE_CHECKING:
    from chatapi.discord.town_hall import TownHall
    from engine.player import Player
    from engine.tribunal import Tribunal


@dataclass
class Tombstone:
    actor: Actor
    turn_phase: TurnPhase
    turn_number: int
    epitaph: str


class Game:

    def __init__(self, config: T.Dict[str, T.Any] = None):
        self._config = config or dict()
        self._actors: T.List["Actor"] = []  # MUST BE ORDERED STRICTLY
        self._players: T.List["Player"] = []  # MUST BE ORDERED STRICTLY
        self._game_phase = GamePhase.INITIALIZING
        self._turn_number = 1
        self._turn_phase = TurnPhase.INITIALIZING
        self._tribunal: "Tribunal" = None
        self._role_factory = RoleFactory(config=config.get('role', {}))

        self._messenger: T.Optional[Messenger] = None
        self._graveyard: T.List[Tombstone] = list()

        # these are general rules. Some roles can override (e.g blackmailer)
        self._allow_chat = False
        self._allow_pm = False

        self._party_planned: bool = False

        self._town_hall: "TownHall" = None
        self._death_report: DeathReporter = DeathReporter(self)

        # mapping of jailor to prisoner
        self._jail_map: T.Dict["Actor", "Actor"] = dict()

    def to_proto(self) -> state_pb2.Game:
        game = state_pb2.Game(
            game_phase=self.game_phase.name,
            turn_phase=self.turn_phase.name,
            turn_number=self.turn_number,
            tribunal=self.tribunal.to_proto()
        )
        game.actors.extend([a.to_proto() for a in self.get_actors()])
        # TODO: graveyard
        return game

    def transform_actor_role(self, actor: "Actor", role_klass: T.Type[Role]) -> None:
        role = self._role_factory.create_role(role_klass)
        actor._role = role
        actor._visible_role = role  # apply original?

    @property
    def party_ongoing(self) -> bool:
        # TODO: implement party host!
        return False

    @property
    def can_jail(self) -> bool:
        """
        Jail is eligible when:
            * no lynches done in the previous day
            * no party planned for the night
        """
        if self._party_planned:
            return False
        for tombstone in self._graveyard:
            if tombstone.turn_number == self._turn_number and tombstone.actor.lynched:
                return False
        return True

    def prepare_jail(self, jailor: "Actor", prisoner: "Actor") -> None:
        self._jail_map[jailor] = prisoner
        # just give the prisoner a bulletproof vest
        prisoner._vest_active = True

    @property
    def town_hall(self) -> "TownHall":
        return self._town_hall

    @property
    def days_of_peace(self) -> int:
        """
        Count the number of days since the last tombstone was processed
        """
        if not self._graveyard:
            return self.turn_number - 1
        return self._turn_number - max([ts.turn_number for ts in self._graveyard])

    @town_hall.setter
    def town_hall(self, value: "TownHall") -> None:
        if self._town_hall is not None:
            raise ValueError("TownHall already set")
        self._town_hall = value

    def assign_roles(self, roles: T.List["Role"]) -> None:
        """
        Assign roles to players and create actors
        """
        if len(roles) != len(self._players):
            raise ValueError("Mismatched number of roles and players")

        for idx, role in enumerate(roles):
            print(f"Assigning role {role.name} to {self._players[idx].name}")
            self._actors.append(Actor(self._players[idx], role, self))

    def debug_override_role(self, player_name: str, role_name: str) -> None:
        """
        Override role for a player
        """
        for actor in self._actors:
            if actor.name == player_name:
                break
        else:
            print(f"Could not find actor with name {player_name}")
            return

        from engine.role.base import RoleFactory
        rf = RoleFactory(self._config.get("roles", {}))
        role = rf.create_by_name(role_name)
        print(f"Making {player_name} a {role_name}")
        actor._role = role

    def get_live_actors_by_role(self, role_klass: T.Type['Role']) -> T.List["Actor"]:
        return [actor for actor in self._actors if actor.is_alive and isinstance(actor.role, role_klass)]

    def get_actor_by_name(self, name: str, raise_if_missing: bool = False) -> T.Optional["Actor"]:
        for actor in self._actors:
            if actor.name == name:
                return actor
        if raise_if_missing:
            raise ValueError(f"No actor by name {name}")
        return None

    def get_actor_for_player(self, player: "Player", raise_if_missing: bool = False) -> T.Optional["Actor"]:
        for actor in self._actors:
            if actor._player == player:
                return actor
        if raise_if_missing:
            raise ValueError(f"No actor for player {player}")
        return None

    def add_players(self, *players: "Player") -> None:
        for player in players:
            if player in self._players:
                continue
            self._players.append(player)

    def update_graveyard(self, actor: "Actor") -> None:
        """
        This should get called whenever `kill` is called.
        """
        self._graveyard.append(Tombstone(actor, self._turn_phase, self._turn_number, actor.epitaph))

    def reset_targets(self) -> None:
        for actor in self._actors:
            actor.choose_targets()

    @property
    def graveyard(self) -> T.List["Tombstone"]:
        """
        An ordered list of tombstones. These should be ordered with age (oldest first).
        """
        return self._graveyard

    @property
    def concluded(self) -> bool:
        """
        Do a dynamic evaluation of end conditions

        Games end when any of these conditions is met:
            * All Mafia + Neut Killing + Neut Evil are eliminated
            * 2 Players Left
            * All town are eliminated
            * 3 Days of Peace
        """
        if not self.get_live_evil_actors():
            print("Game ending on no evils left")
            return True
        if not self.get_live_town_actors():
            print("Game ending on no Town left")
            return True
        if len(self.get_live_actors()) == 2:
            print("Game ending on 1v1")
            return True
        if self.days_of_peace >= 3:
            print("Game ending on days of peace stalemate")
            return True
        return False

    @property
    def messenger(self) -> T.Optional[Messenger]:
        return self._messenger

    @messenger.setter
    def messenger(self, messenger: Messenger) -> None:
        self._messenger = messenger

    @property
    def death_reporter(self) -> DeathReporter:
        return self._death_report

    @property
    def tribunal(self) -> "Tribunal":
        return self._tribunal

    @tribunal.setter
    def tribunal(self, value: "Tribunal") -> None:
        self._tribunal = value

    @property
    def game_phase(self) -> GamePhase:
        return self._game_phase

    @game_phase.setter
    def game_phase(self, new_phase: GamePhase) -> None:
        if self._game_phase == GamePhase.CONCLUDED:
            raise ValueError("Cannot move a game out of `CONCLUDED`")
        if new_phase == GamePhase.INITIALIZING:
            raise ValueError("Cannot move a game into INITIALIZING")
        self._game_phase = new_phase

    @property
    def turn_number(self) -> int:
        return self._turn_number

    @turn_number.setter
    def turn_number(self, value) -> None:
        self._turn_number = value

    @property
    def turn_phase(self) -> TurnPhase:
        return self._turn_phase

    @turn_phase.setter
    def turn_phase(self, new_phase: TurnPhase) -> None:
        self._turn_phase = new_phase

    def add_actors(self, *actors: "Actor") -> None:
        for actor in actors:
            if actor in self._actors:
                continue
            self._actors.append(actor)

    @property
    def actors(self) -> T.List["Actor"]:
        return [a for a in self._actors]

    @property
    def human_actors(self) -> T.List["Actor"]:
        return [a for a in self._actors if a.player.is_human]

    @property
    def bot_actors(self) -> T.List["Actor"]:
        return [a for a in self._actors if a.player.is_bot]

    @property
    def players(self) -> T.List["Player"]:
        return [p for p in self._players]

    @property
    def human_players(self) -> T.List["Player"]:
        return [p for p in self._players if p.is_human]

    @property
    def bot_players(self) -> T.List["Player"]:
        return [p for p in self._players if p.is_bot]

    def get_actors_with_affiliation(self, affiliation: str) -> T.List["Actor"]:
        return [actor for actor in self._actors if actor.role.affiliation() == affiliation]

    def get_live_town_actors(self) -> T.List["Actor"]:
        return [actor for actor in self._actors if actor.is_alive and actor.role.affiliation() == TOWN]

    def get_live_evil_actors(self) -> T.List["Actor"]:
        return [
            actor for actor in self._actors if actor.is_alive
            and (
                actor.role.affiliation() in (MAFIA, TRIAD)
                or
                RoleGroup.NEUTRAL_EVIL in actor.role.groups()
            )
        ]

    def get_live_serial_killer_actors(self) -> T.List["Actor"]:
        return self.get_live_actors_by_role(SerialKiller)

    def get_live_mass_murderer_actors(self) -> T.List["Actor"]:
        return self.get_live_actors_by_role(MassMurderer)

    def get_live_evil_non_killing_actors(self) -> T.List["Actor"]:
        # TODO: update after auditor / witch / judge
        return []

    def get_actors(self) -> T.List["Actor"]:
        return [actor for actor in self._actors]

    def get_live_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if actor.is_alive]
        if shuffle:
            random.shuffle(out)
        return out

    def get_dead_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if not actor.is_alive]
        if shuffle:
            random.shuffle(out)
        return out

    def get_live_mafia_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if actor.is_alive and actor.role.affiliation() == MAFIA]
        if shuffle:
            random.shuffle(out)
        return out

    def get_live_non_mafia_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if actor.is_alive and actor.role.affiliation() != MAFIA]
        if shuffle:
            random.shuffle(out)
        return out

    def get_live_non_triad_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if actor.is_alive and actor.role.affiliation() != TRIAD]
        if shuffle:
            random.shuffle(out)
        return out

    def get_lynch_votes(self) -> T.Dict["Actor", int]:
        """
        Count the number of lynch votes for each player
        """
        votes = defaultdict(lambda: 0)
        for actor in self._actors:
            lynch_vote = actor._lynch_vote
            if lynch_vote is not None:
                votes[lynch_vote] += actor._vote_count

        # return an explicit dictionary with defaulted values instead of a default dictionary
        return {actor: votes[actor] for actor in self._actors}

    def evaluate_post_game(self) -> T.List["Actor"]:
        winners = []
        for actor in self._actors:
            wc = actor.role.win_condition()
            if wc.evaluate(actor, self):
                winners.append(actor)
        return winners
