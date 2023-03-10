import typing as T

from engine.action.base import Action

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Redirect(Action):
    """
    Force the target to visit another character

    NOTE: if you visit a target with multiple target options, you will
    cause them to not do anything.

    Redirect will affect the first selection target in the case of multiple
    targets. For a Redirect action, this will be the control target.
    """

    ORDER = 15

    def feedback_text_success(self) -> str:
        return "You feel a strange force manipulating you."

    def target_text_success(self) -> str:
        return f"You successfully manipulated {self._action_result.get('controlled', 'UNKNOWN')} " + \
            f"visit {self._action_result.get('target', 'UNKNOWN')}."

    def action_result(self, actor: "Actor", controlled: "Actor", target: "Actor") -> T.Optional[bool]:
        # replace first target only?
        controlled.targets[0] = target
        self._action_result["controlled"] = controlled
        self._action_result["target"] = target
        return True


class Hide(Action):
    """
    Cause anything that targets you to hit your target instead
    """

    ORDER = 30

    def feedback_text_success(self) -> str:
        return f"You hid behind {self._action_result.get('target', 'UNKNOWN')}"

    def target_text_fail(self) -> str:
        """
        Most notably this will fail if your target was killed by a Veteran
        """
        return f"You were unable to hide behind {self._action_result.get('target', 'UNKNOWN')}"

    def target_text_success(self) -> str:
        return f"You notice a pathetic individual cowering in your house"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        """
        This applies pretty early so it should generally succeed.
        """
        # find everybody who's targeting our actor and switch their targets to 
        # the target specified here
        self._action_result['target'] = target.name
        for anon in actor.game.get_live_actors(shuffle=True):
            if actor in anon.targets:
                anon.targets.remove(actor)
                anon.targets.append(target)
        return True
