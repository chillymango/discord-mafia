"""
The resolver is what takes care of handling game engine logic.

After all submissions for actions are closed, each action-target association
is inserted, an execution order is determined, and it's off to the races for
state mutations.
"""
import logging
import typing as T

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.action.base import Action


class SequenceEvent:
    """
    This represents a player issuing an action request.
    """

    def __init__(self, action: "Action", actor: "Actor", targets: T.List["Actor"] = None):
        self._action = action
        self._actor = actor
        self._game = actor.game
        self._targets = targets or actor.targets

    @property
    def log(self) -> logging.Logger:
        return self._game.log

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
            self.log.warning(f"{self._actor} tried to use ability with no ability uses left. Ignoring.")
            return
        if not self._action.validate_targets(self._targets):
            self.log.warning(f"{self._actor} targeting {self._targets} failed to validate")
            return
        success = self._action.do_action(self._actor, *self._targets)
        if success is not None:
            self._actor.role._ability_uses -= 1
        self._action.update_crimes(self._actor, success)
        self._action.message_results(self._actor, success)
