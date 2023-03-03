"""
The resolver is what takes care of handling game engine logic.

After all submissions for actions are closed, each action-target association
is inserted, an execution order is determined, and it's off to the races for
state mutations.
"""
import typing as T

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.action.base import Action


class SequenceEvent:
    """
    This represents a player issuing an action request.
    """

    def __init__(self, action: "Action", actor: "Actor"):
        self._action = action
        self._actor = actor
        self._game = actor.game
        self._targets = actor.targets

    @property
    def actor(self) -> "Actor":
        return self._actor

    @property
    def action(self) -> "Action":
        return self._action

    @property
    def targets(self) -> T.List["Actor"]:
        return self._targets

    def execute(self) -> None:
        """
        Execute this event.
        """
        self._action.reset_results()
        if not self._actor.has_ability_uses:
            print("WARN: trying to execute ability without uses. How did this happen")
            return
        self._action.validate_targets(self._targets)
        success = self._action.do_action(self._actor)
        if success is not None:
            self._actor.role._ability_uses -= 1
        self._action.update_crimes(self._actor, success)
        self._action.message_results(self._actor, success)
