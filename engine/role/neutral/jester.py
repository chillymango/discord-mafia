from engine.action.annoy import Annoy
from engine.action.base import ActionSequence
from engine.role.neutral import NeutralRole


class Jester(NeutralRole):

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A lunatic whose life's goal is to be publicly executed."

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
        return "Annoy another player, indicating to that player that they were " + \
               "visited by a Jester."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [Annoy]
