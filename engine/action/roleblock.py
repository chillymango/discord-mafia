import typing as T
from engine.action.base import Action
from engine.crimes import Crime

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Roleblock(Action):
    """
    Block a player action
    """

    ORDER = 10

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.SOLICITING],
            False: [Crime.SOLICITING],
        }


    def feedback_text_success(self) -> str:
        return "You successfully roleblocked your target."

    def feedback_text_fail(self) -> str:
        return "You went to occupy their night, but they turned you away. Your target is roleblock immune!"

    def target_text_success(self) -> str:
        return "An attractive individual approached you to occupy your night. You were roleblocked!"

    def target_text_fail(self) -> str:
        if self._action_result.get("intercepted", False):
            return "An attractive individual approached you to occupy your night, but you have other plans for them..."
        return "An attractive individual approached you to occupy your night, but you turned them away."

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        """
        Publish a private message to our actor with results.
        """
        self.reset_results()
        self._action_result["intercepted"] = False

        # if your target has redirect_roleblockers enabled, you will silently
        # redirect them to target you (E E E K)
        # TODO: private attr access
        if target.role._intercept_rb:
            # they should visit you instead
            # NOTE: the way this works for multiple roleblockers on an interceptor is that
            # the last one to process will get the retarget. The others should get a roleblock
            # immune message.
            target.choose_targets(actor)
            self._action_result["intercepted"] = True
            return False
        if target.role._rb_immune:
            return False

        # roleblock logic should be to switch target to None if roleblock is successful
        target.reset_target()
        return True
