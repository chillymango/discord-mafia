"""
Kill-Report
"""
import logging
import typing as T

from engine.message import Message
import log

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game
    from engine.message import Messenger


logger = logging.getLogger(__name__)
logger.addHandler(log.ch)
logger.setLevel(logging.INFO)


class DeathReporter:
    """
    Something attached to the game that uses game messenger to report
    deaths as appropriate.
    """

    def __init__(self, game: "Game") -> None:
        self._game = game
        self._dead_players: T.Set[Actor] = set()

    @property
    def messenger(self) -> "Messenger":
        return self._game.messenger

    def report_all_deaths(self) -> None:
        for dead in self._game.get_dead_actors():
            self.report_death(dead)

    def create_report(self, actor: "Actor") -> Message:
        if actor._last_will is None:
            lw = "We could not find their last will."
        elif actor._last_will == "":
            lw = "They did not leave a last will."
        else:
            lw = actor._last_will

        if actor._visible_role is not None:
            role = actor._visible_role.name
        else:
            role = "Unable to be determined"

        mark = (f"{actor.epitaph}\n\n"
                f"**Role**:\n{role}\n\n"
                f"**Last Will**:\n{lw}")
        if actor._corpse_death_note:
            mark += f"\n\n**Death Note**:\n{actor._corpse_death_note}"

        return Message.announce(
            self._game,
            f"{actor.name} Has Died",
            mark
        )

    def release_all_new_deaths(self) -> T.Iterator[Message]:
        """
        Figure out all death reports and return an iterator over them.

        Generates a message for each
        """
        for actor in self._game.get_dead_actors(shuffle=True):
            if actor in self._dead_players:
                continue
            self._dead_players.add(actor)
            yield self.create_report(actor)

    def report_death(self, actor: "Actor", force: bool = False) -> None:
        """
        Issue a message describing an Actor death.

        If `force` is False (default), it will not report the death of a player
        that has already been reported. Otherwise, it will always report the death.
        """
        if actor.is_alive:
            print("WARNING: trying to report death of live player")
            return

        if actor in self._dead_players and not force:
            return

        self._dead_players.add(actor)

        self.messenger.queue_message(self.create_report(actor))
