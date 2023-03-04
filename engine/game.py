import asyncio
import random
import typing as T
from collections import defaultdict

from engine.actor import Actor
from engine.affiliation import MAFIA
from engine.affiliation import TRIAD
from engine.report import KillReport
from engine.message import Messenger
from engine.phase import GamePhase
from engine.phase import TurnPhase
from proto import state_pb2

if T.TYPE_CHECKING:
    from engine.player import Player
    from engine.role.base import Role
    from engine.tribunal import Tribunal


class Game:

    def __init__(self, config: T.Dict[str, T.Any] = None):
        self._config = config or dict()
        self._actors: T.List["Actor"] = []  # MUST BE ORDERED STRICTLY
        self._players: T.List["Player"] = []  # MUST BE ORDERED STRICTLY
        self._game_phase = GamePhase.INITIALIZING
        self._turn_number = 1
        self._turn_phase = TurnPhase.INITIALIZING
        self._tribunal: "Tribunal" = None

        self._messenger: T.Optional[Messenger] = None
        self._kill_report = KillReport()

        # these are general rules. Some roles can override (e.g blackmailer)
        self._allow_chat = False
        self._allow_pm = False

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

    def get_actor_by_name(self, name: str) -> T.Optional["Actor"]:
        for actor in self._actors:
            if actor.name == name:
                return actor
        return None

    def get_actor_for_player(self, player: "Player") -> T.Optional["Actor"]:
        for actor in self._actors:
            if actor._player == player:
                return actor
        return None

    def add_players(self, *players: "Player") -> None:
        for player in players:
            if player in self._players:
                continue
            self._players.append(player)

    def announce(self, message: str) -> None:
        if self._messenger is None:
            print(message)
        else:
            self._messenger.announce(message)

    @property
    def concluded(self) -> bool:
        """
        Do a dynamic evaluation of end conditions
        """
        return False

    @property
    def kill_report(self) -> KillReport:
        return self._kill_report

    @property
    def messenger(self) -> T.Optional[Messenger]:
        return self._messenger

    @messenger.setter
    def messenger(self, messenger: Messenger) -> None:
        self._messenger = messenger

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
    def players(self) -> T.List["Player"]:
        return [p for p in self._players]

    def get_actors_with_affiliation(self, affiliation: str) -> T.List["Actor"]:
        return [actor for actor in self._actors if actor.affiliation == affiliation]

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

    def get_live_non_mafia_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if actor.is_alive and actor.affiliation != MAFIA]
        if shuffle:
            random.shuffle(out)
        return out

    def get_live_non_triad_actors(self, shuffle: bool = False) -> T.List["Actor"]:
        out = [actor for actor in self._actors if actor.is_alive and actor.affiliation != TRIAD]
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

    def flush_all_messages(self, delay: float = None) -> None:
        """
        Probably want to code in more gradual transitions here eventually
        """
        if self._messenger is None:
            print("No messenger. Skipping messages")
            return

        # always drive private messages instantly
        asyncio.ensure_future(self.messenger.drive_all_private_queues())

        # drive public messages with specified delay for dramatic effect
        asyncio.ensure_future(self.messenger.drive_public_queue())
        
