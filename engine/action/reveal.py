import typing as T

from engine.action.base import Action
from engine.message import Message

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Reveal(Action):
    """
    Publicly reveal the role of a person
    """

    def message_results(self, actor: "Actor", success: bool) -> None:
        """
        Issue a public message to the town that you have revealed your role as a base.
        """
        if success:
            actor.game.messenger.queue_message(Message.announce(
                actor.game,
                f"{actor.name} the {actor.role.name}",
                f"{actor.name} has revealed themselves as the {actor.role.name}!"
            ))
