"""
A bot that largely behaves randomly
"""
from donbot import DonBot


class RandoBot(DonBot):
    """
    This bot will more or less act randomly based on the inputs it receives.

    It will generate generic text.

    When it detects that it has some choice, it will randomly select a choice.
    """
