from engine.action.base import ActionSequence
from engine.action.kill import MassMurder
from engine.role.neutral import NeutralRole


class MassMurderer(NeutralRole):

    default_night_immune = True

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A crazed spree killer who thinks entrail-spilling is an art form."

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
        return "Perform a killing spree at someone's house each night, " + \
               "killing anyone who visits that player at night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [MassMurder]
