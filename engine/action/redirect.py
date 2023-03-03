from engine.action.base import Action


class Redirect(Action):
    """
    Force the target to visit another character
    """


class Hide(Redirect):
    """
    Cause anything that targets you to hit your target instead
    """
