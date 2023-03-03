from engine.action.base import ActionSequence
from engine.action.kill import SerialKillerKill
from engine.action.nou import NoU
from engine.role.neutral import NeutralRole


class SerialKiller(NeutralRole):

    default_night_immune = True
    default_rb_immune = True
    default_intercept_rb = True

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "A deranged criminal who hates the world."

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
        return "Choose one target to kill each night."

    @classmethod
    def night_actions(cls) -> ActionSequence:
        return [SerialKillerKill]
