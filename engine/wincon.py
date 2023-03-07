import typing as T

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game


class WinCondition:
    """
    Evaluated at end of game to see if a player won the game or not.
    """

    @classmethod
    def description(cls) -> str:
        return "This is a placeholder. If you're seeing this please contact the game developers."

    def evaluate(self, actor: "Actor", game: "Game") -> bool:
        """
        Return True if the condition is satisfied and False if not
        """
        raise NotImplementedError(f"Win condition {self.__class__.__name__} is not implemented")


class TownWin(WinCondition):
    """
    Town wins if there are no evils and no Mafia / Triad left
    """

    @classmethod
    def description(cls) -> str:
        return "You win with the town. " + \
            "You win if there are no Town members left alive, there are no Triad members alive, " + \
            "and there are no Neutral Killing members left alive. You are able to win with " + \
            "Neutral Evil characters. You lose if there are no Mafia members left alive."


class MafiaWin(WinCondition):
    """
    Mafia wins if there are no Town, no killing-evil, and no Triad
    """

    @classmethod
    def description(cls) -> str:
        return "You win with the Mafia. " + \
            "You win if there are no Town members left alive, there are no Triad members alive, " + \
            "and there are no Neutral Killing members left alive. You are able to win with " + \
            "Neutral Evil characters. You lose if there are no Mafia members left alive."


class TriadWin(WinCondition):
    """
    Triad wins if there are no Town, no killing-evil, and no Mafia
    """

    @classmethod
    def description(cls) -> str:
        return "You win with the Triad. " + \
            "You win if there are no Town members left alive, there are no Mafia members alive, " + \
            "and there are no Neutral Killing members left alive. You are able to win with " + \
            "Neutral Evil characters. You lose if there are no Triad members left alive."


class JesterWin(WinCondition):
    """
    Jester wins if he was lynched by the Town
    """

    @classmethod
    def description(cls) -> str:
        return "You win if you are lynched. If you are killed at night, or shot by the Constable, " + \
            "you do not win. If you are not dead at the end of the game, you will lose." 


class SurvivorWin(WinCondition):
    """
    Survivor wins if still alive at end of game
    """

    @classmethod
    def description(cls) -> str:
        return "You do not care if the Town wins or the Mafia wins. You win if you are alive at " + \
            "the end of the game. You lose if you are killed during the game."


class ExecutionerWin(WinCondition):
    """
    Executioner wins if their target was lynched
    """

    @classmethod
    def description(cls) -> str:
        return "You win if your target is lynched by the town. If your target is killed by " + \
            "other means, you will become a Jester."


class AutoVictory(WinCondition):
    """
    If I fuck up just take the W
    """

    @classmethod
    def description(cls) -> str:
        return "Someone forgot to give your role a win condition. You automatically win. Sorry!"
