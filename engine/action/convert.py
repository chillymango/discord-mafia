from engine.action.transform import Transform


class ConvertCultist(Transform):
    """
    Do a series of pre-checks to determine success and what not
    """


class ConvertMason(Transform):
    """
    Check if target is a citizen. If so, convert to Mason.
    If target is Mafia / Triad, issue notification to them.
    """
