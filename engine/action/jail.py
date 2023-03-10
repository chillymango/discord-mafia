import typing as T

from engine.action.base import Action
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Jail(Action):
    """
    Put somebody in jail and optionally execute them.

    This one's going to be a pain to implement but I'm really excited!

    Jail is a day action.
    """

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.MURDER],
            False: [Crime.TRESPASSING],
        }

    def target_title(self, success: bool) -> str:
        return "You've Been Jailed"

    def feedback_text_success(self) -> str:
        return "You successfully detained your target.\nSee the thread to chat with them."

    def feedback_text_fail(self) -> str:
        return "You failed to detain your target."

    def target_text_success(self) -> str:
        return "Someone blindfolded you and dragged you off into solitary confinement.\n" + \
            "See the thread to chat with them."

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        if actor.game.can_jail:
            actor.game.prepare_jail(actor, target)
            # refund the ability use since we only deduct if we execute
            actor.role._ability_uses += 1
            return True
