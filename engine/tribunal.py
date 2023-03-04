"""
Trial System
"""
import asyncio
from enum import Enum
import time
import typing as T
from collections import defaultdict

from engine.component import Component
from engine.phase import GamePhase
from engine.phase import TurnPhase
from proto import state_pb2

if T.TYPE_CHECKING:
    from chatapi.discord.view import ViewController
    from engine.actor import Actor
    from engine.game import Game
    from engine.message import Messenger


class TrialType:
    STANDARD = 0
    MULTI = 1


class TribunalState(Enum):

    CLOSED = 0  # Tribunal is closed to all external interactions
    TRIAL_VOTE = 1  # Tribunal is open to trial voting
    TRIAL_DEFENSE = 2  # Tribunal is closed to trial voting
    LYNCH_VOTE = 3  # Tribunal is open to lynch voting
    JURY_VERDICT = 4  # Tribunal is announcing whether to lynch, and giving a chance for last words
    LYNCH_VERDICT = 5  # Tribunal is announcing the player's role and last will


class Tribunal(Component):
    """
    General base class that can probably just be used straight up

    Inheriting classes can make overrides based on game rules.
    """

    def __init__(self, game: "Game", tribunal_config: T.Dict[str, T.Any]) -> None:
        self._game = game
        self._config = tribunal_config
        self._state = TribunalState.CLOSED

        self._on_trial: "Actor" = None

        # judge sets this to True during Court
        self._anonymous: bool = False

        # the voting result to skip the day
        self._skip_vote: T.Set["Actor"] = set()

        # the voting result to put somebody on trial
        self._trial_vote: T.Dict["Actor", "Actor"] = dict()

        # the voting result to lynch somebody
        self._lynch_vote: T.Dict["Actor", "Actor"] = dict()

        # the number of votes each player gets
        # TODO: i set to 10 for albert debug
        self._vote_count: T.Dict["Actor", int] = defaultdict(lambda: 10)  # e.g Mayor / Judge can edit this

        self._trial_type = TrialType.STANDARD
        self._lynches_left: int = 1  # Marshall can modify this for a turn

        # call this to edit the last output
        self._view_controller: "ViewController" = None

        # TODO: populate some trial timings and what not
        self._day_duration = self._config.get("day_duration", 60.0)
        self._defense_period = self._config.get("defense_period", 20.0)
        self._lynch_vote_period = self._config.get("lynch_vote_period", 15.0)

        # lynching on day 1 is troll
        self._skip_first_day = self._config.get("skip_first_day", True)

        # marshall config
        self._marshall_lynches = self._config.get("marshall_lynches", 3)

        # keep track of who the judge and mayor are
        self._judge: T.Optional["Actor"] = None
        self._mayor: T.Optional["Actor"] = None

    def to_proto(self) -> state_pb2.Tribunal:
        tribunal = state_pb2.Tribunal()
        tribunal.state = self.state.name
        tribunal.trial_votes.extend([
            state_pb2.VoteCount(player=player, count=count)
            for player, count in self._trial_vote.items()
        ])
        tribunal.lynch_votes.extend([
            state_pb2.VoteCount(player=player, count=count)
            for player, count in self._lynch_vote.items()
        ])
        tribunal.skip_votes = self.skip_vote_counts
        return tribunal

    @property
    def state(self) -> TribunalState:
        return self._state

    @property
    def view_controller(self) -> "ViewController":
        return self._view_controller
    
    @view_controller.setter
    def view_controller(self, vc: "ViewController") -> None:
        self._view_controller = vc

    @property
    def messenger(self) -> "Messenger":
        return self._game.messenger

    def mayor_action(self, mayor: "Actor", votes: int = 4) -> bool:
        # the mayor can always reveal
        # TODO: make it a configurable option that if the Mayor's role changes
        # they lose their extra votes
        self._vote_count[mayor] = votes
        self._mayor = mayor
        return True

    def marshall_action(self) -> bool:
        if self._state in (TribunalState.JURY_VERDICT, TribunalState.LYNCH_VERDICT):
            # do not allow Marshall to activate if Voting has passed
            return False
        self._trial_type = TrialType.MULTI
        self._lynches_left += self._marshall_lynches - 1
        return True

    def judge_action(self, judge: "Actor", votes: int = 4) -> bool:
        if self._state in (TribunalState.JURY_VERDICT, TribunalState.LYNCH_VERDICT):
            # do not allow Judge to activate if Voting has passed
            return False
        self._judge = judge
        self._trial_type = TrialType.MULTI
        self._anonymous = True
        self._vote_count[judge] = votes
        return True

    def reset(self) -> None:
        """
        Run this reset during Dusk or after a lynch vote.
        """
        self._lynches_left = 1
        self._anonymous = False
        self._on_trial = None
        self._trial_type = TrialType.STANDARD
        self.reset_votes()

    def reset_votes(self) -> None:
        self._skip_vote = set()
        self._trial_vote = dict()
        self._lynch_vote = dict()
        self._vote_count.pop(self._judge)

    @property
    def trial_quorum(self) -> int:
        """
        Number of people required for a trial vote to actually put someone on trial.

        Should be floor(live_players / 2) + 1
        """
        return len(self._game.get_live_actors()) / 2 + 1

    async def drive_view(self) -> None:
        if self._view_controller is not None:
            await self.view_controller.drive()

    async def do_daylight(self) -> None:
        """
        Run the daylight procedures for the Tribunal
        """
        if self._game.turn_phase != TurnPhase.DAYLIGHT:
            return

        self._state = TribunalState.TRIAL_VOTE
        await self.drive_view()
        t_init = time.time()
        print('Starting tribunal')
        # we should do something here where every time we change states, we tell our View to change
        # institute a maximum timeout, but don't cancel the Tribunal early if it's exceeded
        while (time.time() - t_init < self._day_duration) or self.trial_ongoing:
            if self._state == TribunalState.TRIAL_VOTE:
                if self.maybe_go_to_trial():
                    if self._trial_type == TrialType.MULTI:
                        # set the person to insta lynch
                        self._state = TribunalState.JURY_VERDICT
                    else:
                        self._state = TribunalState.TRIAL_DEFENSE
                    
                elif self.maybe_skip_day():
                    self._state = TribunalState.CLOSED

            elif self._state == TribunalState.TRIAL_DEFENSE:
                # TODO: add input controls here
                await asyncio.sleep(self._defense_period)
                self._state = TribunalState.LYNCH_VOTE

            elif self._state == TribunalState.LYNCH_VOTE:
                # TODO: add input controls here
                await self.drive_view()
                await asyncio.sleep(self._lynch_vote_period)
                self._state = TribunalState.JURY_VERDICT

            elif self._state == TribunalState.JURY_VERDICT:
                if self.should_lynch:
                    self.messenger.announce(
                        f"The town has voted to lynch {self._on_trial.name}\n"
                        f"By a vote of {self.lynch_yes_votes} to {self.lynch_no_votes}\n"
                        f"{'' if self._anonymous else self.lynch_tally()}",
                        flush=True
                    )
                    self.reset_votes()
                    await asyncio.sleep(5.0)
                    self._state = TribunalState.LYNCH_VERDICT
                else:
                    self.messenger.announce(
                        f"The town has voted to acquit {self._on_trial.name}\n"
                        f"By a vote of {self.lynch_yes_votes} to {self.lynch_no_votes}\n"
                        f"{'' if self._anonymous else self.lynch_tally()}",
                        flush=True
                    )
                    self.reset_votes()
                    await asyncio.sleep(5.0)
                    self._state = TribunalState.TRIAL_VOTE

            elif self._state == TribunalState.LYNCH_VERDICT:
                self.messenger.announce(f"May your soul rest in peace, {self._on_trial.name}", flush=True)
                await asyncio.sleep(2.0)

                # TODO: add to kill report too
                self._on_trial.kill()

                # do not announce imediately
                self.messenger.announce(f"{self._on_trial.name}'s role was {self._on_trial.role.name}")
                self._lynches_left -= 1
                await asyncio.sleep(10.0)
                if self._lynches_left > 0:
                    self.messenger.announce(f"We have {self._lynches_left} remaining lynches.", flush=True)
                    self._state = TribunalState.TRIAL_VOTE
                else:
                    self.messenger.announce(f"We have no remaining lynches today.", flush=True)
                    self._state = TribunalState.CLOSED
                    break

            # check ten times a second? ooooooof
            await asyncio.sleep(0.1)
        else:
            # debug print
            print("Trial timed out")
            self.messenger.announce("It's getting late. Let's reconvene tomorrow.", flush=True)
            return
        # debug print
        print("Trial concluded?")

    @property
    def show_lynch_vote_view(self) -> bool:
        return self._state == TribunalState.LYNCH_VOTE

    @property
    def show_trial_vote_view(self) -> bool:
        return self._state == TribunalState.TRIAL_VOTE

    @property
    def trial_ongoing(self) -> bool:
        """
        Returns True if the trial is on-going. This is so the primary driver does not transition
        out of Daylight if there is an active trial.
        """
        return self._state in (
            TribunalState.TRIAL_DEFENSE,
            TribunalState.LYNCH_VOTE,
            TribunalState.JURY_VERDICT,
            TribunalState.LYNCH_VERDICT,
        )

    def _count_votes(self, votes: T.Dict["Actor", "Actor"]) -> T.Dict["Actor", int]:
        counts: T.Dict["Actor", int] = defaultdict(lambda: 0)
        for voter, voted in votes.items():
            counts[voted] += self._vote_count[voter]
        return counts

    @property
    def trial_vote_counts(self) -> T.Dict["Actor", int]:
        return self._count_votes(self._trial_vote)

    @property
    def skip_vote_counts(self) -> int:
        vote_count = 0
        for voter in self._skip_vote:
            vote_count += self._skip_vote[voter]
        return vote_count

    @property
    def lynch_yes_votes(self) -> int:
        count = 0
        for voter, voted in self._lynch_vote.items():
            if voted:
                count += self._vote_count[voter]
        return count

    @property
    def lynch_no_votes(self) -> int:
        count = 0
        for voter, voted in self._lynch_vote.items():
            if voted == False:
                count += self._vote_count[voter]
        return count

    @property
    def should_lynch(self) -> bool:
        """
        Check if the lynch vote succeeds or not.

        If we're in a Multi-lynch situation (either Court or Marshall), just return True
        """
        if self._trial_type == TrialType.MULTI:
            return True
        
        if self.lynch_yes_votes > self.lynch_no_votes:
            return True
        return False

    def lynch_tally(self) -> str:
        """
        Get the string that describes the lynch votes.
        """
        output = ""
        for actor in self._game.get_live_actors():
            raw = self._lynch_vote.get(actor)
            if raw:
                res = "GUILTY"
            elif raw == False:
                res = "INNOCENT"
            else:
                res = "ABSTAIN"

            output += f"\t**{actor.name}** voted **{res}**\n"
        return output

    def maybe_skip_day(self) -> bool:
        """
        Check if the skip vote has received quorum.

        If the vote count has been met, return True to skip the day.
        """
        if self.skip_vote_counts > self.trial_quorum:
            self.messenger.announce("The town has voted to skip trials today.", flush=True)
            return True
        return False

    def maybe_go_to_trial(self) -> bool:
        """
        Check if any player has received quorum.

        If there is a player that has received quorum, return True to transition to the Trial phase.
        """
        for target, counts in self.trial_vote_counts.items():
            # there's a possibility here of a tie condition here, but in that case
            # we will just select the first one we see
            if counts >= self.trial_quorum:
                self._on_trial = target
                self.messenger.announce(f"The town has voted to put {target.name} on trial     ({counts} votes)", flush=True)
                self.messenger.private_actor(target, "The town has voted to put you on trial!", flush=True)
                return True
        return False

    def submit_trial_vote(self, voter: "Actor", voted: "Actor") -> None:
        self._trial_vote[voter] = voted
        self._skip_vote.discard(voter)
        if voted is None:
            self.messenger.announce(f"{voter.name} has cleared their vote", flush=True)
        else:
            self.messenger.announce(f"{voter.name} has voted to put {voted.name} on trial", flush=True)

    def submit_skip_vote(self, voter: "Actor") -> None:
        self._trial_vote[voter] = None
        self._skip_vote.add(voter)
        self.messenger.announce(f"{voter.name} has voted to skip the day")

    def submit_lynch_vote(self, voter: "Actor", vote: T.Optional[bool]) -> None:
        self.messenger.announce(f"{voter.name} has cast a ballot", flush=True)
        self._lynch_vote[voter] = vote
