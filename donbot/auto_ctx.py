from dataclasses import dataclass
import typing as T

from donbot.action import BotAction
from donbot.action import ActionInference
from donbot.action import TrialVote
from donbot.action import LynchVote
from donbot.action import DayAction
from donbot.action import NightAction
from engine.affiliation import MAFIA
from engine.affiliation import TRIAD
from engine.role.base import TargetGroup
from engine.phase import TurnPhase
from engine.role import NAME_TO_ROLE
from engine.role.base import Role
from engine.setup import DEFAULT_CONFIG
from engine.tribunal import TribunalState
from proto import state_pb2


class AutomationContext:
    """
    This is something we keep that roughly tells us what the bot is supposed to be doing.

    It's also probably important for the context object here to figure out what the possible
    choices are. That way it can delegate the decision making to another object.

    For example:
        Daylight:
            * respond to Tribunal depending on the current state.
            * if has Day action, consider using Day action.
            * (ChatGPT) record user input and respond to it as necessary
            * issue PMs and respond to PMs
        Night:
            * perform night actions as appropriate.
            * investigative town roles should
    """

    def __init__(self, bot_name: str, actors: T.List[state_pb2.Actor], turn_phase: TurnPhase, turn_number: int, tribunal: state_pb2.Tribunal) -> None:
        self.bot_name = bot_name
        for actor in actors:
            if actor.player.name == bot_name:
                self.actor = actor
                break
        else:
            raise ValueError("We are not part of this game")

        self.actors = actors
        self.turn_phase = turn_phase
        self.turn_number = turn_number
        self.tribunal = tribunal
        self.tribunal_state = TribunalState[self.tribunal.state]

    @classmethod
    def create_from_game_proto(cls, bot_name: str, game_proto: state_pb2.Game) -> "AutomationContext":
        # TODO: make a constructor or something for this
        ctx = cls(bot_name, game_proto.actors, TurnPhase[game_proto.turn_phase], game_proto.turn_number, game_proto.tribunal)
        return ctx

    @property
    def role(self) -> T.Optional[T.Type["Role"]]:
        return NAME_TO_ROLE.get(self.actor.role.name.replace(' ', ''))

    def infer_actions(self) -> T.List[BotAction]:
        """
        Figure out what the game is allowing us to do right now.

        No-Op is always an option.
        """
        actions = [BotAction.NO_OP]
        if self.turn_phase == TurnPhase.DAYBREAK:
            actions.extend([BotAction.SEND_PRIVATE_MESSAGE, BotAction.SEND_PUBLIC_MESSAGE])

        elif self.turn_phase == TurnPhase.DAYLIGHT:
            actions.extend([BotAction.SEND_PUBLIC_MESSAGE, BotAction.SEND_PRIVATE_MESSAGE])
            if self.role is None:
                print("Role unknown. Assuming no actions.")
            elif len(self.role.day_actions()) > 0 and self.actor.role.ability_uses != 0:
                actions.append(BotAction.DAY_ACTION)

            if self.tribunal_state == TribunalState.TRIAL_VOTE:
                actions.extend([BotAction.TRIAL_VOTE, BotAction.SEND_PUBLIC_MESSAGE])
            if self.tribunal_state == TribunalState.TRIAL_DEFENSE:
                pass
            if self.tribunal_state == TribunalState.LYNCH_VOTE:
                actions.extend([BotAction.LYNCH_VOTE, BotAction.SEND_PUBLIC_MESSAGE])

        elif self.turn_phase == TurnPhase.NIGHT:
            if self.role is None:
                print("Role unknown. Assuming no actions.")
            elif len(self.role.night_actions()) > 0 and self.actor.role.ability_uses != 0:
                actions.append(BotAction.NIGHT_ACTION)

        return actions

    def get_targets(self, as_str: bool = True) -> T.List[str]:
        # these are all protos lol
        if self.actor.is_alive:
            role = self.role(DEFAULT_CONFIG)
            if role.target_group == TargetGroup.LIVE_PLAYERS:
                targets = [ac for ac in self.actors if ac.is_alive]
            elif role.target_group == TargetGroup.DEAD_PLAYERS:
                targets = [ac for ac in self.actors if not ac.is_alive]
            elif role.target_group == TargetGroup.LIVING_NON_MAFIA:
                targets = [ac for ac in self.actors if ac.is_alive and ac.role.affiliation != MAFIA]
            elif role.target_group == TargetGroup.LIVING_NON_TRIAD:
                targets = [ac for ac in self.actors if ac.is_alive and ac.role.affiliation != TRIAD]
            elif role.target_group == TargetGroup.SELF:
                # special group, either activate ability or no
                targets = ["YES", "NO"]
            else:
                targets = []

            # manually handle self-targeting
            if role.allow_self_target and self.actor not in targets:
                targets.append(self.actor)
            elif not role.allow_self_target and self.actor in targets:
                targets.remove(self.actor)
            
            if as_str:
                return [targ.player.name if isinstance(targ, state_pb2.Actor) else str(targ) for targ in targets]

            return targets

        return []

    def infer_targets(self, actions: T.Iterable[BotAction]) -> T.Dict[BotAction, T.List[T.Any]]:
        """
        For each of the actions provided, infer the possible targets that we can assess.

        TODO: this can / should probably go in another class...?
        """
        targets: T.Dict[BotAction, T.List[T.Any]] = dict()
        for action in actions:
            targets[action] = list()

            if action == BotAction.NO_OP:
                targets[action] = [None]
                continue

            # target live players
            if action in (
                BotAction.SEND_PRIVATE_MESSAGE,
                BotAction.SEND_PUBLIC_MESSAGE,
            ):
                # TODO: eventually will need to block if we get blackmailed or something
                # but for now I'm very happy to just ignore that
                targets[action] = [ac.player.name for ac in self.actors if ac.is_alive]
                continue

            if action == BotAction.TRIAL_VOTE:
                targets[action] = [ac.player.name for ac in self.actors if ac.is_alive]
                if self.bot_name in targets[action]:
                    targets[action].remove(self.bot_name)
                continue

            # boolean(ish) choice
            if action in (BotAction.LYNCH_VOTE, BotAction.SKIP_VOTE):
                targets[action] = [True, False, None]
                continue

            # role targets?
            # we can / should try to re-use the target group spec
            if self.role is None:
                continue

            if action in (BotAction.DAY_ACTION, BotAction.NIGHT_ACTION):
                # just look at target group for role
                # TODO: needing to instantiate here is bad
                targets[action] = self.get_targets()
                continue

        return targets
