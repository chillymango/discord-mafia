"""
Brought to you by ChatGPT

A session is basically a single instance of a game.
"""
import asyncio
import time
import typing as T

from chatapi.app.bot_api import BotApi
from chatapi.app.grpc.api import api
from chatapi.app.grpc.run import run_grpc_server
from chatapi.discord.forward import ForwardChatMessages
from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.driver import DiscordPublicDriver
from chatapi.discord.driver import DiscordPrivateDriver
from chatapi.discord.driver import WebhookDriver
from chatapi.discord.icache import icache
from chatapi.discord.router import router
from chatapi.discord.town_hall import TownHall
from engine.game import Game
from engine.message import Messenger
from engine.phase import GamePhase
from engine.phase import TurnPhase
from engine.player import Player
from engine.setup import EXAMPLE_CONFIG
from engine.setup import do_setup
from engine.stepper import sleep_override
from engine.stepper import Stepper

if T.TYPE_CHECKING:
    import disnake


class Session:

    def __init__(
        self,
        guild: "disnake.Guild",
        config: T.Dict[str, T.Any] = EXAMPLE_CONFIG
    ) -> None:
        self._guild = guild
        self._config = config
        self._server_task: asyncio.Task = None

        self._game = Game(config)
        self._stepper = Stepper(self._game, self._config)
        self._skipper = Stepper(self._game, self._config, sleeper=sleep_override)

        self._bot_driver = None
        self._discord_driver = None
        self._webhook_driver = None

        self._town_hall = TownHall(self._game, self._guild)
        self._game.town_hall = self._town_hall

        self._game_task: asyncio.Task = None

    @property
    def bulletin(self) -> T.Optional["disnake.TextChannel"]:
        return self._town_hall.ch_bulletin

    def add_players(self, *players) -> None:
        self._game.add_players(*players)

    async def ui_loop(self) -> None:
        """
        TODO: this is dumb
        """
        period = 1.0
        while not self._game.concluded:
            t_i = time.time()
            await self._town_hall.drive()
            delta = time.time() - t_i
            if delta > period:
                print(f"WARNING: UI loop lagging, took {delta}s but we allocated {period}s")
            await asyncio.sleep(max(period - delta, 0.0))

    async def game_loop(self) -> None:
        print("Started game loop")
        while not self._game.concluded:
            await self._stepper.step()

    async def start(self) -> None:
        result, msg = do_setup(self._game)
        if not result:
            raise RuntimeError(f"Failed to setup game: {msg}")
        self._game.debug_override_role("chilly mango", "Constable")
        self._game.debug_override_role("asiannub", "Veteran")

        #self._server_task = asyncio.create_task(run_grpc_server(self._game))
        api.set_bot_api(BotApi(self._game))

        self._town_hall.initialize()
        await self._town_hall.prepare_for_game()

        # create message drivers for our game
        drivers = [
            DiscordPublicDriver(self._town_hall.ch_bulletin),
            await WebhookDriver.create_with_name(self._game, self._town_hall.ch_bulletin, "Botspeak")
        ]
        drivers.extend([DiscordPrivateDriver(self._town_hall.ch_bulletin, ac) for ac in self._game.human_actors])
        drivers.extend([BotMessageDriver(bot) for bot in self._game.bot_actors])
        self._messenger = Messenger(self._game, *drivers)
        self._game.messenger = self._messenger
        self._messenger.start()

        # start game
        self._game.game_phase = GamePhase.IN_PROGRESS
        await self._town_hall.display_welcome()
        await asyncio.sleep(3.0)

        # set it to Dusk
        #self._game.turn_phase = TurnPhase.DUSK

        await asyncio.gather(self.game_loop(), self.ui_loop())
