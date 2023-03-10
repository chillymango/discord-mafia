import typing as T

from engine.action.base import Action
from engine.message import Message

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Protect(Action):
    """
    Bodyguard protection

    BG fights off assailant and both die

    NOTE: this should not inherit from `Kill` because we don't want BG protect
    to be counted as a Killing action. This would make two BGs who target the
    same individual kill each other, which is almost certainly undesired.
    """

    # apply these before kill orders so if their HP dips to zero or below we pop them
    ORDER = 90

    @property
    def kill_damage(self) -> int:
        return 1

    def attack(self, actor: "Actor") -> None:
        """
        Do the attack transaction
        """
        actor._attacked_by.append(self.__class__)
        actor.hitpoints -= self.kill_damage
        if actor.hitpoints <= 0:
            actor.kill()

    def announce(self):
        return "You hear the harsh sounds of an old-fashioned shootout"

    @classmethod
    def kill_report_text(cls) -> str:
        return "Killed in a duel."

    def feedback_text_success(self) -> str:
        return "Your target was attacked tonight! You fight off the attacker."

    def target_text_success(self) -> str:
        return "You were attacked tonight, but a Bodyguard arrived to fight off your attacker!"

    def intercept_text(self) -> str:
        return "You went to kill your target, but a Bodyguard stood in your way and challenged you to fight!"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        # find the first attacker who targeted your target
        # TODO: fix circ import
        from engine.role import KILLING_ROLES

        # if multiple attacker matches, randomize the one that actually gets selected for intercept
        for anon in actor.game.get_live_actors(shuffle=True):
            if actor == anon:
                continue
            if target in anon.targets and type(anon.role) in KILLING_ROLES and anon.is_alive:
                # always ignore immunity, just inflict damage
                self.attack(anon)
                self.attack(actor)
                # also actually perform an interception
                anon.choose_targets(actor)
                self._action_result["intercepted"] = anon
                return True
        return None

    def message_results(self, actor: "Actor", success: bool) -> None:
        """
        Also let the assailant know they were intercepted
        """
        attacker: "Actor" = self._action_result.get("intercepted")
        if attacker is not None:
            attacker.game.messenger.queue_message(
                Message.private_feedback(attacker, "Intercepted!", self.intercept_text())
            )

        return super().message_results(actor, success)
