import random
import typing as T


if T.TYPE_CHECKING:
    from donbot import DonBot
    from donbot.action import BotAction


class Call:
    """
    This is the output from the resolve.

    It should specify what method to call and the args to pass it.
    """

    @classmethod
    def create_from_no_op(cls) -> "Call":
        return cls()


class Resolver:
    """
    Some way of making decisions.

    Resolvers are given a set of input choices and must resolve a single
    output decision.

    TODO: should this have some sort of state? Probably not...?
    For the fully random I don't think it'll really matter
    For the ChatGPT one we expect ChatGPT to keep track
    """

    def __init__(self, arg_count: int = 1) -> None:
        self._count = arg_count

    def resolve(self, options: T.Dict[str, T.Any]) -> T.List[Call]:
        raise NotImplementedError("Child classes must implement")


class RandomResolver(Resolver):
    """
    Make choices randomly.

    This is literally random. It's going to play very poorly.
    """

    def resolve(self, options: T.List[T.Any], count: int = 1) -> T.List[T.Any]:
        return random.sample(options, count)
