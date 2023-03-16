"""
Brought to you by ChatGPT

A session is basically a single instance of a game.
"""
import asyncio
import logging
import time
import typing as T

from chatapi.app.bot_api import BotApi
from chatapi.app.grpc.api import api
from chatapi.app.grpc.run import run_grpc_server
from chatapi.discord.channel import channel_manager
from chatapi.discord.forward import ForwardChatMessages
from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.driver import DiscordPublicDriver
from chatapi.discord.driver import DiscordPrivateDriver
from chatapi.discord.driver import WebhookDriver
from chatapi.discord.game import GAMES
from chatapi.discord.icache import icache
from chatapi.discord.router import router
from chatapi.discord.town_hall import TownHall
from engine.game import Game
from engine.message import Message
from engine.message import Messenger
from engine.phase import GamePhase
from engine.phase import TurnPhase
from engine.player import Player
from engine.setup import DEFAULT_CONFIG
from engine.setup import do_setup
from engine.stepper import sleep_override
from engine.stepper import Stepper
from engine.wincon import MassMurdererWin
from engine.wincon import SerialKillerWin
from engine.wincon import TownWin
from engine.wincon import MafiaWin
from engine.wincon import SurvivorWin
from engine.wincon import ExecutionerWin
from engine.wincon import JesterWin

if T.TYPE_CHECKING:
    import disnake
    from engine.config import GameConfig


class Session:

    def __init__(
        self,
        guild: "disnake.Guild",
        config: "GameConfig "= DEFAULT_CONFIG
    ) -> None:
        self._guild = guild
        self._config = config
        self._server_task: asyncio.Task = None

        self._game = Game(config)
        self._stepper = Stepper(self._game)
        self._skipper = Stepper(self._game, sleeper=sleep_override)

        self._town_hall = TownHall(self._game, self._guild)
        self._game.town_hall = self._town_hall

        self._game_task: asyncio.Task = None

    @property
    def log(self) -> logging.Logger:
        return self._game.log

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

        # step until daylight
        while not self._game.turn_phase in (TurnPhase.DAYLIGHT, TurnPhase.DUSK):
            await self._stepper.step()

    async def start(self) -> None:
        setup_attempt_count = 0
        while setup_attempt_count <= 3:
            setup_attempt_count += 1
            result, msg = do_setup(self._game)
            if not result:
                self.log.warning(f"Failed to setup game: {msg}")
                continue
            break
        else:
            raise ValueError("Failed to setup game. Setup is likely unstable")

        # TODO: block this out somewhere else
        #self._game.debug_override_role("donbot", "Executioner")
        #self._game.debug_override_role("asiannub", "Vigilante")
        #self._game.debug_override_role("donbot", "Blackmailer")
        #self._game.debug_override_role("mmmmmmmmmmmmm", "Mayor")
        #self._game.debug_override_role("pandomodger", "Judge")
        #self._game.debug_override_role("mimitchi", "Jailor")
        #self._game.debug_override_role("wagyu jubei", "Blackmailer")
        #self._game.debug_override_role("wagyu jubei")

        api.set_bot_api(BotApi(self._game))

        self._town_hall.initialize()
        await self._town_hall.prepare_for_game()
        self._game.log.name = f"Game-{self._town_hall.ch_bulletin.name}"

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

        # if the game starts, lets store it
        GAMES[self._town_hall.ch_bulletin] = self._game

        # start game
        self._game.game_phase = GamePhase.IN_PROGRESS
        await self._town_hall.display_welcome()

        await asyncio.sleep(5.0)

        await self._town_hall.display_role_setup()

        await asyncio.sleep(5.0)

        ui_task = asyncio.create_task(self.ui_loop())
        await self.game_loop()
        ui_task.cancel()

        # game should be over now, evaluate win conditions
        winners = self._game.evaluate_post_game()

        # figure out the highest "score" of win condition
        # manually do a check here i guess...
        win_conditions = set(winner.role.win_condition() for winner in winners)

        priority = [
            SerialKillerWin,
            MassMurdererWin,
            MafiaWin,
            TownWin,
            ExecutionerWin,
            SurvivorWin,
            JesterWin,
        ]
        for wc in priority:
            if wc in win_conditions:
                break
        else:
            raise ValueError(f"Unknown Win Condition. Valid ones: {win_conditions}")

        # create win condition screen with primary win condition
        self._messenger.queue_message(Message.announce(self._game, "We have reached a conclusion..."))
        await asyncio.sleep(8.0)
        await self._town_hall.display_victory(winners, wc)
        await asyncio.sleep(5.0)
        await self._town_hall.display_original_roles()
        channel_manager.mark_to_preserve(self._town_hall.ch_bulletin)
        self.log.info("FIN")
