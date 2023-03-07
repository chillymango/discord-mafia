from engine.action.base import Action


class Lynch(Action):
    """
    This is really just for epitaph
    """

    @classmethod
    def kill_report_text(cls) -> str:
        return "Lynched."
