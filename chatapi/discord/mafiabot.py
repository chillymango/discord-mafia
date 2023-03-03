# This example requires the 'message_content' privileged intent to function.
import asyncio

import time
import typing as T
from typing import List
from disnake.ext import commands
from disnake.interactions import Interaction
import disnake

from chatapi.discord.router import Router
from chatapi.discord.lobby import Lobby
from chatapi.discord.lobby import LobbyState
from engine.game import Game
from engine.player import Player
from engine.phase import GamePhase

if T.TYPE_CHECKING:
    from discord.user import User
    from discord.channel import TextChannel
    from discord.guild import Guild
    from engine.actor import Actor


# testing
from chatapi.discord.input_panel import InputPanel
from engine.setup import do_setup

TOKEN = 'MTA3OTg1MDUzNjUwMjgyOTEzNg.GokFWW.MrfXK8bZGcJ_wG09yiAKjvVMiXIy-rnOMLU8pI'


class MafiaBot(commands.Bot):
    def __init__(self):
        intents = disnake.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('/'), intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def close(self):
        for lobby in lobby_manager.values():
            if lobby.state != LobbyState.CLOSED:
                await lobby.close_lobby()
        await super().close()


class FakeUser:
    """
    Not everybody can be real during dev...

    Make the prints for these just go to another user?
    """


bot = MafiaBot()
router = Router()
bot.add_listener(router.on_button_click)
bot.add_listener(router.on_string_select, name="on_dropdown")

# TODO: store these with server ID as a unique key
game = None
lobby_embed: disnake.Embed = None
lobby_message: disnake.Message = None

lobby_manager: T.Dict[disnake.Guild, Lobby] = dict()


async def lobby_subparser(player: "Player", interaction, command: str, args: str) -> None:
    global bot
    interaction: "Interaction" = interaction
    if command == "create-game":
        if interaction.guild in lobby_manager:
            if lobby_manager[interaction.guild] == LobbyState.OPEN:
                await interaction.response.send_message(
                    f"There is already a game in progress. If you are not in the game, try join-game instead"
                )
                return
        try:
            lobby = Lobby(router, debug=True)
            await lobby.open_lobby(interaction)
            lobby_manager[interaction.guild] = lobby
        except BaseException:  # if creation fails, do not block another re-attempt
            lobby_manager.pop(interaction.guild)
        await lobby.add_player(interaction)

    elif command == "join-game":
        if interaction.guild not in lobby_manager:
            return await interaction.response.send_message("No game in progress. Create one first.", ephemeral=True)
        lobby = lobby_manager[interaction.guild]
        await lobby.add_player(interaction)

    elif command == "add-bot":
        print('adding a bot')
        fake_player = Player("bot")
        game.add_players(fake_player)
        await interaction.response.send_message("Added a bot", ephemeral=True)

    elif command == "show-lobby":
        await interaction.response.send_message(
            "Lobby:\n\t" + "\n\t".join([p.name for p in game.players]), ephemeral=True
        )

    else:
        await interaction.response.send_message(f"Invalid command {command}", ephemeral=True)


async def game_subparser(player, interaction, command: str, args: str) -> None:
    if command == "status":
        # bring up the current game state
        await interaction.response.send_message("")

    elif command in ("last-will", "lw", "lastwill", "will"):
        # TODO: update last will
        await interaction.response.send_message("Last Will successfully updated")

    elif command == "countdown-30s":
        # test a command to countdown for 30s then delete the message
        countdown_to = int(time.time() + 30.0)
        await interaction.response.send_message(f"<t:{countdown_to}:R>", ephemeral=True, delete_after=30.0)

    elif command == "valid-targets":
        actor: "Actor" = game.get_actor_for_player(player)
        options = actor.get_target_options()
        await interaction.response.send_message(
            f"You can target:\n\t" + "\n\t".join([f'[{anon.number}] {anon.name}' for anon in options])
        )

    elif command == "target":
        actor: "Actor" = game.get_actor_for_player(player)
        to_target = args.split()
        target_array = list()
        for target in to_target:
            target_actor = None
            try:
                target = int(target)
            except ValueError:
                # try to find by name
                try:
                    target = game.get_actor_by_name(target)
                except ValueError:
                    pass
            if target is None:
                await interaction.response.send_message(
                    f"Unable to resolve {target} as a valid target. Please check valid targets."
                )
                return
            target_array.append(target_actor)
        actor.choose_targets(*target_array)


@bot.slash_command(description="Interact with a Mafia Game")
async def mafia(interaction, command_input: str):
    """Play Mafia or something"""
    global game
    interaction: Interaction = interaction
    command, _, args = command_input.partition(' ')

    lobby = lobby_manager.get(interaction.guild)
    if command == "test":
        print('test command')
        game = Game()
        # add user and 15 bots
        user = interaction.user
        p = Player(user.name)
        game.add_players(p)
        for _ in range(14):
            bot_player = Player("random bot name")
            game.add_players(bot_player)
        result, msg = do_setup(game)
        print(result)
        print(msg)
        actor = game.get_actor_for_player(p)
        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(label="haha hi"))
        teststr = """```ansi
\u001b[0;40m\u001b[1;32mThat's some cool formatted text right?
or
\u001b[1;40;32mThat's some cool formatted text right?
```"""
        await interaction.send(content=teststr)
        #panel = InputPanel(user, game, actor.role)
        #await interaction.send(**panel.export_to_discord(), ephemeral=True)
    elif lobby is None or lobby.state in (LobbyState.OPEN, LobbyState.CLOSED):
        await lobby_subparser(interaction.user, interaction, command, args)
    elif lobby.state == LobbyState.STARTED:
        await game_subparser(interaction.user, interaction, command, args)
print('wait what did i brek')
bot.run(TOKEN)
