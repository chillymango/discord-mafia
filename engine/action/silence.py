import typing as T

from engine.actor import Actor
from engine.action.base import Action


class Silence(Action):
    """
    Prevent somebody from speaking during the next day.

    Cannot blackmail people who are night immune.
    """

    # blackmail goes before vet (20) but after swaps (10ish)
    ORDER = 15

    def feedback_text_fail(self) -> str:
        return "Your target was too much for you. You were unable to blackmail them."

    def feedback_text_success(self) -> str:
        return "You successfully blackmailed your target."

    def target_text_success(self) -> str:
        return f"A sinister man approached you and threatened to reveal some hideous " + \
            "secrets of yours!"

    def target_title(self, success: bool) -> str:
        return "You've Been Blackmailed"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        if not target.is_alive:
            return None

        # this silences human players
        actor.game.town_hall.silence(target)

        # this silences bot players
        # TODO: bots don't talk right now anyways
        return True
