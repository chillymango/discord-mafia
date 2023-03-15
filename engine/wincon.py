import logging
import typing as T

from engine.action.lynch import Lynch
import log

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log.ch)


class WinCondition:
    """
    Evaluated at end of game to see if a player won the game or not.
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "Unknown Victory. This is a BUG."

    @classmethod
    def description(cls) -> str:
        return "This is a placeholder. If you're seeing this please contact the game developers."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Return True if the condition is satisfied and False if not
        """
        raise NotImplementedError(f"Win condition {cls.__name__} is not implemented")


class TownWin(WinCondition):
    """
    Town wins if there are no evils and no Mafia / Triad left
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Town Has Won"

    @classmethod
    def description(cls) -> str:
        return "You win with the town. " + \
            "You win if there are no Mafia members left alive, there are no Triad members alive, " + \
            "and there are no Neutral Evil members left alive. You lose if there are no Town members " + \
            "left alive."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Evaluate in the following order:
            * if there are no Town members left alive, Town loses
            * if any Evil group outnumbers Town, Town loses
            * if none of the above, Town wins
        """
        if not len(game.get_live_town_actors()):
            return False
        if len(game.get_live_mafia_actors()) >= len(game.get_live_town_actors()):
            return False
        if len(game.get_live_serial_killer_actors()) >= len(game.get_live_town_actors()):
            return False
        if len(game.get_live_mass_murderer_actors()) >= len(game.get_live_town_actors()):
            return False
        if len(game.get_live_evil_non_killing_actors()) >= len(game.get_live_town_actors()):
            return False
        return True


class MafiaWin(WinCondition):
    """
    Mafia wins if there are no Town, no killing-evil, and no Triad
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Mafia Have Won"

    @classmethod
    def description(cls) -> str:
        return "You win with the Mafia. " + \
            "You win if there are no Town members left alive, there are no Triad members alive, " + \
            "and there are no Neutral Killing members left alive. You are able to win with " + \
            "Neutral Evil characters. You lose if there are no Mafia members left alive."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Evaluate in the following order:
            * if there are no Mafia members left alive, the Mafia loses
            * if the Town outnumbers the Mafia, the Mafia loses
            * if any neutral killing group outnumbers the Mafia, the Mafia loses
            * otherwise, the Mafia wins
        """
        if not len(game.get_live_mafia_actors()):
            return False
        if len(game.get_live_town_actors()) > len(game.get_live_mafia_actors()):
            # mafia wins ties over Town (unless cit?)
            return False
        if len(game.get_live_serial_killer_actors()) >= len(game.get_live_mafia_actors()):
            # SK wins ties over Mafia
            return False
        if len(game.get_live_mass_murderer_actors()) >= len(game.get_live_mafia_actors()):
            return False
        return True


class TriadWin(WinCondition):
    """
    Triad wins if there are no Town, no killing-evil, and no Mafia
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Triad Has Won"

    @classmethod
    def description(cls) -> str:
        return "You win with the Triad. " + \
            "You win if there are no Town members left alive, there are no Mafia members alive, " + \
            "and there are no Neutral Killing members left alive. You are able to win with " + \
            "Neutral Evil characters. You lose if there are no Triad members left alive."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        # TODO: implement Triad
        return False


class JesterWin(WinCondition):
    """
    Jester wins if he was lynched by the Town
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Jester Has Won"

    @classmethod
    def description(cls) -> str:
        return "You win if you are lynched. If you are killed at night, or shot by the Constable, " + \
            "you do not win. If you are not dead at the end of the game, you will lose." 

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        if Lynch in actor._attacked_by and not actor.is_alive:
            return True
        return False


class ExecutionerWin(WinCondition):
    """
    Executioner wins if their target was lynched
    """

    @classmethod
    def title(cls) -> str:
        return "The Executioner Has Won"

    @classmethod
    def description(cls) -> str:
        return "You do not care if the Town wins or the Mafia wins. You win if your target is " + \
            "lynched while you are alive. You lose if your target dies without being lynched, or " + \
            "you die while your target remains unlynched."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Evaluate in the following order
        * if the executioner target does not exist, default to True
            * we don't blame players for shitty coding from the dev
        * if the executioner target is still alive, return False
        * if the execution target was lynched and the executioner did not
            die before the target, return True
        * otherwise return False
        """
        target: "Actor" = getattr(actor.role, "executioner_target", None)
        if target is None:
            logger.warning(f"Executioner {actor.name} in game {game} does not have a target at all")
            # default to giving them the win if there's a bug
            return True

        if not target.lynched:
            return False

        # this implies that the target was lynched, so they should be in the graveyard
        # look up when people died. graveyard should already be sorted in order of death time
        if target.lynched and not actor.is_alive:
            for tombstone in reversed(game._graveyard):
                if tombstone.actor == actor:
                    return True
                if tombstone.actor == target:
                    return False

            logger.warning(f"Executioner {actor.name} in game {game} failed to evaluate target "
                        f"from graveyard. Target: {target.name}.\nGraveyard:\n{game._graveyard}")
            # default to giving them the win if there's a bug
            return True

        return True


class SurvivorWin(WinCondition):
    """
    Survivor wins if still alive at end of game
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Survivor Has Won"

    @classmethod
    def description(cls) -> str:
        return "You do not care if the Town wins or the Mafia wins. You win if you are alive at " + \
            "the end of the game. You lose if you are killed during the game."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        if actor.is_alive:
            return True
        return False


class SerialKillerWin(WinCondition):
    """
    Serial killer wins if they're the only killing group left and they outnumber others
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Serial Killer Has Won"

    @classmethod
    def description(cls) -> str:
        return "You must eliminate all members of the Town and the Mafia. " + \
            "You win if there are no Town members left alive, there are no Triad members alive, " + \
            "and there are no Mafia members left alive. You are able to win with " + \
            "Neutral Evil characters."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Evaluate in the following order:
            * if the Serial Killer is dead, they lose
            * if they are outnumbered by the Town, they lose
            * if the Town outnumbers the Mafia, the Mafia loses
            * if any neutral killing group outnumbers the Mafia, the Mafia loses
            * otherwise, the Mafia wins
        """
        if not actor.is_alive:
            return False
        if len(game.get_live_town_actors()) > len(game.get_live_serial_killer_actors()):
            # Town loses tiebreaker to SK
            return False
        if len(game.get_live_mass_murderer_actors()) > len(game.get_live_serial_killer_actors()):
            # MM loses tiebreaker to SK
            # TODO: this should probably be programmable
            return False
        if len(game.get_live_mafia_actors()) > len(game.get_live_serial_killer_actors()):
            # Mafia loses tiebreaker to SK
            return False
        return True


class MassMurdererWin(WinCondition):
    """
    Mass Murderer wins if they're the only killing group left and they outnumber others
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Mass Murderer Has Won"

    @classmethod
    def description(cls) -> str:
        return "You must eliminate all members of the Town and the Mafia. " + \
            "You win if there are no Town members left alive, there are no Triad members alive, " + \
            "and there are no Mafia members left alive. You are able to win with " + \
            "Neutral Evil characters."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Evaluate in the following order:
            * if the MM is dead, they lose
            * if they are outnumbered by the Town, they lose
            * if the Town outnumbers the Mafia, the Mafia loses
            * if any neutral killing group outnumbers the Mafia, the Mafia loses
            * otherwise, the Mafia wins
        """
        if not actor.is_alive:
            return False
        if len(game.get_live_town_actors()) > len(game.get_live_mass_murderer_actors()):
            # Town loses tiebreaker to MM
            return False
        if len(game.get_live_serial_killer_actors()) >= len(game.get_live_mass_murderer_actors()):
            # MM loses tiebreaker to SK
            # TODO: this should probably be programmable
            return False
        if len(game.get_live_mafia_actors()) > len(game.get_live_mass_murderer_actors()):
            # Mafia loses tiebreaker to MM
            return False
        return True


class AutoVictory(WinCondition):
    """
    If I fuck up just take the W
    """

    @classmethod
    def title(cls) -> str:
        """
        Panel title at game presentation
        """
        return "The Autovictory Has Won?"

    @classmethod
    def description(cls) -> str:
        return "Someone forgot to give your role a win condition. You automatically win. Sorry!"

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        return True


class EvilWin(WinCondition):
    """
    Non-Killing Neutral Evil wins if Town has lost.
    """

    @classmethod
    def title(cls) -> str:
        return "The Judge Has Won"

    @classmethod
    def description(cls) -> str:
        return "You win if the Town is eliminated. You must remain alive until the end of the " + \
            "game in order to claim victory. You are able to win with any of the non-Town factions."

    @classmethod
    def evaluate(cls, actor: "Actor", game: "Game") -> bool:
        """
        Evaluate in the following order
            * if the Judge is dead, they lose
            * if the Town has won, they lose
            * otherwise, they Win
        """
        if not actor.is_alive:
            return False
        if TownWin.evaluate(actor, game):  # this is safe to pass in a non-Town actor to evaluate atm
            return False
        return True
