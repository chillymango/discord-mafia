import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.follow import Follow
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Detective(TownRole):
    """
    Detective follows someone and gets who they visited
    """

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A skilled tracker, learning important information on behalf of the town."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "Your role does not have a day action."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "Track one target's activity each night, seeing who they visit."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [Follow]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_INVESTIGATIVE]

    def _role_specific_config_init(self) -> None:
        self._ignores_detect_immunity = self._config.role_config.detective.ignores_detection_immunity
