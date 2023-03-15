import typing as T

from engine.action.base import Action
from engine.action.base import ActionSequence
from engine.action.base import TargetGroup
from engine.action.jail import Jail
from engine.action.kill import JailorKill
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Jailor(TownRole):
    """
    Jailor selects somebody to jail during the day.

    At night, they can choose to execute the person.

    Jail action during day should fix target at night.
    """

    default_ability_uses = 3

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A jail guard officer, secretly detaining suspects."

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "Choose someone to Jail and Rollblock the following night.\n" + \
            "This action only takes effect if nobody is lynched during the day."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "Speak anonymously with the jailed player, and optionally execute that player."

    @classmethod
    def day_actions(cls) -> ActionSequence:
        return [Jail]

    @classmethod
    def night_actions(cls) -> ActionSequence:
        """
        How does ActionSequence work?
        * if you have multiple targets, everything in the first sequence is done to target 1
        * then everything in the second sequence is done to target 2
        * we can work out the number of targets allowed based on what this looks like
        """
        return [JailorKill]

    @property
    def target_group(self) -> TargetGroup:
        return TargetGroup.JAIL

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_POWER, RoleGroup.TOWN_KILLING]

    def _role_specific_config_init(self) -> None:
        self._ability_uses = self._config.role_config.jailor.number_of_executions_available
