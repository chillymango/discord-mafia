from enum import Enum
import typing as T

from donbot.resolver import Resolver

if T.TYPE_CHECKING:
    from donbot import DonBot


class BotAction(Enum):
    NO_OP = 0
    SEND_PUBLIC_MESSAGE = 1
    SEND_PRIVATE_MESSAGE = 2
    TRIAL_VOTE = 3
    LYNCH_VOTE = 4
    SKIP_VOTE = 5
    DAY_ACTION = 6
    NIGHT_ACTION = 7
    LEAVE_GAME = 8  # I really just figure we'll do this if ChatGPT has an existential crisis


class ActionInference:
    """
    Something that encapsulates what we are able to do right now as well as
    well as how to choose an output.

    The valid actions we are able to take at this time are `Call` objects. These
    represent outbound gRPC calls.

    One example of a fulfillment mechanism would be to randomly choose.
    Another example would be to ask ChatGPT.
    """

    VALID_ACTIONS: T.Tuple[BotAction] = ()

    def __init__(self, bot: "DonBot", resolver_klass: T.Type[Resolver]):
        self._bot = bot
        self._resolver = resolver_klass(self._bot)

    def execute(self, **kwargs) -> None:
        raise NotImplementedError("Child classes must define this")

    def run(self) -> T.Dict[str, T.Any]:
        """
        Subclasses need to implement this method to actually perform the required action.
        """
        if self._resolver is None:
            raise ValueError(f"{self.__class__.__name__} does not have a resolver")
        self.execute(**self._resolver.resolve())


class TrialVote(ActionInference):
    """
    Choose to vote to put somebody on trial.

    Options are:
    * pick somebody
    * pick nobody
    * pick to skip
    """

    VALID_ACTIONS = (BotAction.TRIAL_VOTE, BotAction.SKIP_VOTE)


class LynchVote(ActionInference):
    """
    Choose whether to lynch somebody.

    Options are:
    * yes
    * no
    * abstain
    """

    VALID_ACTIONS = (BotAction.LYNCH_VOTE, )


class DayAction(ActionInference):
    """
    Choose whether to perform a day action.
    """

    VALID_ACTIONS = (BotAction.DAY_ACTION, )


class NightAction(ActionInference):
    """
    Choose whether to perform a night action.
    """

    VALID_ACTIONS = (BotAction.NIGHT_ACTION, )
