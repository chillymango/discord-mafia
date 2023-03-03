"""
Brought to you by ChatGPT

A session is basically a single instance of a game.
"""
import typing as T

from engine.loop import LoopDriver
from engine.game import Game
from engine.phase import GamePhase
from engine.player import Player
from engine.setup import do_setup


class Session:
    """
    Instantiate this with a config I guess?

    Setup Order of Operations:
    * create this object
    * create game, loop driver
    * add players
    * run component setup
    * start game

    It seems extremely wasteful to have to do ticks in a turn-based game.
    So we should aim to not do that...

    OK how does this sound?
    * whenever someone makes an input, we call the `drive` method here
    Q: how do we make it so not everybody gets a driven update if a single person issues an update?
    * fuck it lets just not organize it like that at all
    * throw components out the window
    * use this as an aggregate for all the things we need to run a game i guess
    """

    def __init__(self, config: T.Dict[str, T.Any]) -> None:
        self._config = config
        self._game = Game()
        self._driver = LoopDriver(self._game)
        result, msg = do_setup(self._game)

    def add_players(self, *players: Player) -> None:
        self._game.add_players(*players)

    @property
    def game(self) -> Game:
        return self._game

    @property
    def loop_driver(self) -> LoopDriver:
        return self._driver

    def start_game(self) -> bool:
        if self._game.game_phase == GamePhase.INITIALIZING:
            self._game.game_phase = GamePhase.IN_PROGRESS
            return True
        return False
