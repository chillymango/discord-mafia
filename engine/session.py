"""
Brought to you by ChatGPT

A session is basically a single instance of a game.
"""
import asyncio
import typing as T

from chatapi.discord.forward import ForwardChatMessages
from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.driver import DiscordDriver
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

        self._game = Game(config)
        self._stepper = Stepper(self._game, self._config)
        self._skipper = Stepper(self._game, self._config, sleeper=sleep_override)

        self._bot_driver = None
        self._discord_driver = None
        self._webhook_driver = None

        self._town_hall = TownHall(self._game, self._guild)

        self._game_task: asyncio.Task = None

    @property
    def bulletin(self) -> T.Optional["disnake.TextChannel"]:
        return self._town_hall.ch_bulletin

    def add_players(self, *players) -> None:
        self._game.add_players(*players)

    async def loop(self) -> None:
        print("Started game loop")
        # set it to Dusk
        self._game.turn_phase = TurnPhase.DUSK

        while not self._game.concluded:
            await self._stepper.step()

    async def start(self) -> None:
        result, msg = do_setup(self._game)
        if not result:
            raise RuntimeError(f"Failed to setup game: {msg}")

        self._bot_driver = BotMessageDriver()
        self._discord_driver = DiscordDriver(self.bulletin)
        self._webhook_driver = WebhookDriver(self.bulletin)
        self._messenger = Messenger(self._game, self._discord_driver, self._bot_driver, self._webhook_driver)
        self._messenger.start_inbound()
        self._game.messenger = self._messenger
        await self._town_hall.setup_channels()
        self._message_forwarding = ForwardChatMessages(self._bot_driver, self._game, self.bulletin)
        self._message_forwarding.enable_forwarding()

        self._game_task = asyncio.create_task(self.loop())
