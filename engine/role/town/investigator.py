import typing as T

from engine.action.base import ActionSequence
from engine.action.investigate import InvestigateCrimes
from engine.action.investigate import PreInvestigate
from engine.role.base import RoleGroup
from engine.role.town import TownRole


class Investigator(TownRole):
    """
    Investigate crime record.

    I guess we could also support a version that gets exact role eventually?
    """

    ORDER = 1500

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A private sleuth, discreetly aiding the townsfolk."

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
        return "Check one player each night for that player's criminal record."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [PreInvestigate, InvestigateCrimes]

    @classmethod
    def groups(cls) -> T.List[RoleGroup]:
        return super().groups() + [RoleGroup.TOWN_INVESTIGATIVE]
