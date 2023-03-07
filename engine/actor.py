"""
Data class which contains all information associated with an active player (actor)
in a single game.
"""
import typing as T

from engine.action.base import TargetGroup
from engine.action.lynch import Lynch
from engine.affiliation import MAFIA
from engine.affiliation import NEUTRAL
from engine.affiliation import TOWN
from engine.affiliation import TRIAD
from engine.crimes import Crime
from engine.message import Message
from engine.role.base import RoleGroup
from proto import state_pb2

if T.TYPE_CHECKING:
    from engine.action.kill import Kill
    from engine.game import Game
    from engine.player import Player
    from engine.role.base import Role
    from engine.phase import TurnPhase


class Actor:
    """
    Represents a game player.
    """

    def __repr__(self) -> str:
        return f"{'Dead ' if not self.is_alive else ''}Actor - {self.name} ({self._role})"

    def __init__(self, player: "Player", role: "Role", game: "Game"):
        """
        Role should be an object instantiated and hydrated with game settings.

        The remainder is a standard initialization to blank.
        """
        self._game = game
        self._player = player

        # actual role
        self._role = role

        # role presented on death
        self._death_role = role

        # crimes that show up on standard investigate
        self._crimes = set()

        # last will (should be input by player)
        self._last_will = ""

        # leave a note on kill
        self._death_note = ""

        # lynch vote
        self._lynch_vote: "Actor" = None
        self._vote_count = 1  # some roles can override this

        # target
        self._targets: T.List["Actor"] = []

        # visit history (truth)
        self._target_history: T.Dict[T.Tuple[int, TurnPhase]] = dict()

        # handle jail
        self._is_jailor: bool = False
        self._is_jailed: bool = False

        # whether vest is active
        self._vest_active = False

        # by default we start alive
        self._is_alive = True
        self._attacked_by: T.List[T.Type[Kill]] = []

        # this is mostly an ephemeral calculation
        self.hitpoints = 1
        self._attacked = False

        # keep track of messages to issue to players
        self._message_queue: T.List["Message"] = []

        # keep track of messages that have been issued to players?
        self._mesasge_history: T.List["Message"] = []

    def to_proto(self) -> state_pb2.Actor:
        actor = state_pb2.Actor(
            player=self.player.to_proto(),
            role=self.role.to_proto(),
            is_alive=self.is_alive,
        )
        return actor

    def reset_health(self) -> None:
        # never resurrect
        if not self._is_alive:
            return
        self.hitpoints = 1.0
        self._attacked_by = []

    @property
    def epitaph(self) -> str:
        """
        Return the kill report text for the primary action.
        """
        if not self._attacked_by:
            return "Unable to determine cause of death (BUG)"
        primary = self._attacked_by[0].kill_report_text()
        if len(self._attacked_by) > 1:
            primary += ". After that, they were attacked again."
        return primary

    @property
    def was_attacked(self) -> bool:
        return len(self._attacked_by) > 0

    @property
    def has_day_action(self) -> bool:
        return len(self._role.day_actions()) > 0

    @property
    def has_night_action(self) -> bool:
        return len(self._role.night_actions()) > 0

    @property
    def vests(self) -> int:
        return self._role.vests

    def put_on_vest(self) -> bool:
        if self._role.use_vest():
            self._vest_active = True
            return True
        return False

    def take_off_vest(self) -> None:
        self._vest_active = False

    def consume_vest(self) -> None:
        if self._vest_active:
            self._vest_active = False
            self._role.consume_vest()

    @property
    def has_ability_uses(self) -> bool:
        return self._role._ability_uses != 0

    @property
    def cannot_be_healed(self) -> bool:
        return self._role._cannot_be_healed

    @property
    def number(self) -> T.Optional[int]:
        """
        Since we have the game as a reference we can just look ourselves up
        """
        for idx, anon in enumerate(self._game.get_actors()):
            if anon == self:
                return idx
        raise ValueError("We are not in this game")

    @property
    def investigated_crimes(self) -> T.Set[Crime]:
        """
        Depending on game settings, return something for the investigative crimes check
        """
        if self._role._detect_immune:
            return set()
        return self._crimes

    @property
    def investigated_role(self) -> str:
        """
        Depending on game settings, return something for the investigative role exact check
        """
        if self._role._detect_immune:
            return "Citizen"
        return self._role.__class__.__name__

    @property
    def investigated_suspicion(self) -> str:
        """
        Depending on game settings, return something for the investigative alignment check
        """
        if not self._role._detect_immune and self.affiliation in NEUTRAL:
            # detect exact for neutral killing if enabled
            if RoleGroup.NEUTRAL_KILLING in self._role.groups():
                return self._role.__name__
            return "Not Suspicious"

        if not self._role._detect_immune and self.affiliation in (MAFIA, TRIAD):
            return self.affiliation
        return "Not Suspicious"

    @property
    def investigated_affiliation(self) -> str:
        """
        Depending on game settings, return something for the investigative alignment check
        """
        if self._role._detect_immune:
            return TOWN
        return self.affiliation

    @property
    def game(self) -> "Game":
        return self._game

    @property
    def is_alive(self) -> bool:
        return self._is_alive

    @property
    def targets(self) -> T.List["Actor"]:
        return self._targets

    def get_target_options(self, as_str: bool = True) -> T.List["Actor"]:
        """
        Depending on role, get a set of actors that are valid targets.
        """
        if self.is_alive:
            if self._role.target_group == TargetGroup.LIVE_PLAYERS:
                targets = self._game.get_live_actors()
            elif self._role.target_group == TargetGroup.DEAD_PLAYERS:
                targets = self._game.get_dead_actors()
            elif self._role.target_group == TargetGroup.LIVING_NON_MAFIA:
                targets = self._game.get_live_non_mafia_actors()
            elif self._role.target_group == TargetGroup.LIVING_NON_TRIAD:
                targets = self._game.get_live_non_triad_actors()
            elif self._role.target_group == TargetGroup.SELF:
                targets = [self]
            else:
                targets = []

            # manually handle self-targeting
            if self._role.allow_self_target and self not in targets:
                targets.append(self)
            elif not self._role.allow_self_target and self in targets:
                targets.remove(self)
            
            if as_str:
                return [targ.name for targ in targets]
            return targets
        return []

    def get_lynch_options(self, as_str: bool = False) -> T.List["Actor"]:
        """
        You can always vote for any live player except yourself

        ...wait fuck it make it so you can vote for yourself
        """
        options = self._game.get_live_actors()
        if as_str:
            return [x.name for x in options]
        return options

    def lynch_vote(self, actor: "Actor") -> None:
        self._lynch_vote = actor

    def choose_targets(self, *targets: "Actor") -> None:
        """
        Since this is going to be connected to the chatbot input, we don't do validation
        until we actually need to execute the action. If the action is invalid we'll just
        drop and make sure to return a detailed explanation.
        """
        self._targets = list(targets)

    def reset_target(self) -> None:
        """
        This should run after actions start processing during day and night phase
        """
        self._targets = list()
    
    def reset_lynch_vote(self) -> None:
        """
        This should run when day finishes
        """
        self._lynch_vote = None

    @property
    def name(self) -> str:
        return self._player.name

    @classmethod
    def affiliation(self) -> str:
        """
        Get the actor's affiliation. This may change if role changes (e.g amnesiac)
        """
        return self._role.affiliation()

    def lynch(self) -> None:
        """
        Add the lynch action and then execute a kill
        """
        self._attacked_by = [Lynch]
        self.kill()

    def kill(self) -> None:
        print(f"Killed {self}")
        self._is_alive = False
        # NOTE: we should be able to generate tombstone here since all protective
        # actions should act *before* kills take place
        self._game.update_graveyard(self)

    @property
    def player(self) -> "Player":
        return self._player

    @property
    def role(self) -> "Role":
        return self._role
 
    def add_crimes(self, crimes: T.Iterable["Crime"]) -> None:
        self._crimes.update(crimes)
