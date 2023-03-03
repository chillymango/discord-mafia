"""
Action Base Class
"""
from enum import Enum
import typing as T

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.crimes import Crime


class Action:
    """
    Someday I'll have a big enough brain to sketch this out ahead of time

    But for now I don't :)
    """

    ORDER = 1000

    def __init__(self) -> None:
        """
        Arguments should be targets, keyword arguments should be any other modifiers
        """
        # format output string messages with these results
        self._action_result: T.Dict[str, T.Any] = dict()

    def reset_results(self) -> None:
        """
        Should be called by the stepper or resolver before doing a sequence resolution
        """
        self._action_result = dict()

    def validate_targets(self, *targets: "Actor") -> bool:
        """
        Verify target counts match
        """
        if len(targets) != self.target_count:
            print(f"ERROR: invalid target count for {self.__class__.__name__}. "
                  f"Expected {self.target_count} and got {len(targets)}.")
            return False
        return True

    def action_result(self, actor: "Actor", *targets: "Actor") -> T.Optional[bool]:
        """
        Child classes must override this.

        Returns True to indicate successful action.
        Returns False to indicate an attempted but failed action.
        Returns None to indicate no action.
        """
        raise NotImplementedError(f"Base class {self.__class__.__name__} must define action")

    def do_action(self, actor: "Actor") -> T.Optional[bool]:
        if not actor.targets:
            return None
        valid = actor is not None and self.validate_targets(*actor.targets)
        if not valid:
            return None
        return self.action_result(actor, *actor.targets)

    def update_crimes(self, actor: "Actor", success: bool) -> None:
        """
        Add crimes depending on whether the action committed was successful.
        """
        actor.add_crimes(self.crimes.get(success, []))

    def message_results(self, actor: "Actor", success: bool) -> None:
        if success:
            actor.private_message(self.feedback_text_success())
        elif success == False:
            actor.private_message(self.feedback_text_fail())
        for targ in actor.targets:
            if success:
                targ.private_message(self.target_text_success())
            elif success == False:
                targ.private_message(self.target_text_fail())
        if success and self.announce():
            # if there is text here it should be announced
            actor.game.announce(self.announce())

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        """
        A map of success / fail to possible Crimes that succeed on each
        """
        return {}

    def announce(self) -> str:
        """
        Text fed to the public channel. Generally should only issue if something
        was successful.

        Most actions do not incur an announcement.
        """
        return ""

    def choose_text_success(self, *targets: "Actor", **kwargs: str) -> str:
        """
        Text fed back to the player if their target choosing was successful.
        This should generally succeed.

        This should be issued as a private message.
        """
        return "You targeted {targets}".format(targets)

    def feedback_text_success(self) -> str:
        """
        Text fed back to player if their action(s) were successful.

        This should be issued as a private message.
        """
        return ""

    def feedback_text_fail(self) -> str:
        """
        Text fed back to the player if their action was unsuccessful.

        This should be issued as a private message.
        """
        return ""

    def target_text_success(self) -> str:
        """
        By default, targets aren't told anything about being targeted (either success or fail)

        This should be issued as a private message.
        """
        return ""

    def target_text_fail(self) -> str:
        """
        By default, targets aren't told anything about being targeted (either success or fail).

        This should be issued as a private message.
        """
        return ""

    @classmethod
    def instant(cls) -> bool:
        """
        By default, actions are not instant. They will trigger at some other time.
        """
        return False

    @property
    def target_count(self) -> int:
        return 1


ActionSequence = T.List[T.Type[Action]]


class TargetGroup(Enum):
    LIVE_PLAYERS = 0
    DEAD_PLAYERS = 1
    LIVING_NON_MAFIA = 2
    LIVING_NON_TRIAD = 3
    SELF = 4
