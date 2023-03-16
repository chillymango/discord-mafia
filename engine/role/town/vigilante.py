import typing as T

from engine.action.base import ActionSequence
from engine.action.kill import VigilanteKill
from engine.action.base import TargetGroup
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Vigilante(TownRole):
    """
    Vigilante shoots somebody at night
    """

    default_ability_uses = 2

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A dirty cop who will ignore the law and order to enact justice."

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
        return "Choose one target to kill each night. You cannot kill on the first night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [VigilanteKill]

    @property
    def target_group(self) -> TargetGroup:
        """
        Vig target group is special in that on Night 1 they can't kill
        """
        return TargetGroup.VIGILANTE

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_KILLING]

    def _role_specific_config_init(self) -> None:
        self._ability_uses = self._config.role_config.vigilante.number_of_shots
