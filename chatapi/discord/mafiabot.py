# This example requires the 'message_content' privileged intent to function.
import asyncio
import os
import signal
import time
import typing as T
from typing import List

from disnake.ext import commands
from disnake.interactions import Interaction
from grpc import aio
import disnake

from chatapi.app import app
from chatapi.app.bot_api import BotApi
from chatapi.app.server import run_app_and_bot
from chatapi.app.grpc.api import api
from chatapi.app.grpc.api import GrpcBotApi
from chatapi.discord.channel import channel_manager
from chatapi.discord.chat import CHAT_DRIVERS
from chatapi.discord.game import GAMES
from chatapi.discord.icache import icache
from chatapi.discord.name import NameChanger
from chatapi.discord.router import router
from chatapi.discord.lobby import LobbyState
from chatapi.discord.lobby import NewLobby
from chatapi.discord.permissions import ALL_ROLES
from engine.actor import Actor
from engine.game import Game
from engine.message import Message
from engine.role.mafia.godfather import Godfather
from engine.player import Player
from engine.phase import GamePhase

from proto import service_pb2_grpc

if T.TYPE_CHECKING:
    from discord.user import User
    from discord.channel import TextChannel
    from discord.guild import Guild
    from chatapi.discord.driver import ChatDriver


# testing
from engine.setup import do_setup

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if TOKEN is None:
    raise OSError("No bot token")

_cleanup_coroutines = []


# TODO: why the fuck is this so gross
#grpc_api = GrpcBotApi()
name_changer: NameChanger = None

BIND = 'localhost:50051'


class MafiaBot(commands.Bot):
    def __init__(self):
        intents = disnake.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=commands.when_mentioned_or('-'), intents=intents)

    async def start(self, *args, **kwargs) -> None:
        """
        Before we start the bot, add gRPC into the loop
        """
        global api
        self._api = api
        self._server = aio.server()
        service_pb2_grpc.add_GrpcBotApiServicer_to_server(api, self._server)
        self._server.add_insecure_port(BIND)
        await asyncio.gather(
            super().start(*args, **kwargs),
            self._server.start()
        )

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def close_lobby(self, lobby: "NewLobby") -> None:
        try:
            await lobby.close_lobby()
        except:
            print(f"Failed to close lobby")

    async def close(self):
        # always shut off the anonymous role first if we can
        print("Shutting down server")
        await asyncio.gather(*[
            self.close_lobby(lobby) for lobby in lobby_manager.values() if lobby.state != LobbyState.CLOSED
        ] + [
            channel_manager.shutdown()
        ])
        print("Deleting all added roles")
        await asyncio.gather(*[role.delete() for role in ALL_ROLES])
        # TODO: graceful shutdown
        await super().close()


class FakeUser:
    """
    Not everybody can be real during dev...

    Make the prints for these just go to another user?
    """


lobby_manager: T.Dict[disnake.Guild, NewLobby] = dict()


def main() -> None:
    bot = MafiaBot()
    bot.add_listener(router.on_button_click)
    bot.add_listener(router.on_string_select, name="on_dropdown")
    bot.add_listener(router.on_message)
    bot.add_listener(router.on_modal_submit)

    router.register_button_general_callback(icache.update_with_interaction)
    router.register_string_general_callback(icache.update_with_interaction)

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
                game_channel = await channel_manager.create_channel(interaction.guild, "mafia-bulletin")
                lobby = NewLobby(interaction.guild, game_channel, debug=True)
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

    @bot.slash_command(description="Issue chat to a Mafia Game")
    async def chat(interaction, command_input: str):
        interaction: "disnake.ApplicationCommandInteraction" = interaction
        # try and get chat driver if one exists
        if interaction.channel.type == disnake.ChannelType.public_thread:
            driver = CHAT_DRIVERS.get(interaction.channel.parent)
        else:
            driver = CHAT_DRIVERS.get(interaction.channel)
        if driver is None:
            await interaction.send("Cannot send chat right now", ephemeral=True, delete_after=15.0)
            return
        driver.publish_from_external(interaction.user.name, command_input)
        await interaction.send("Message sent", ephemeral=True, delete_after=0.0)

    @bot.slash_command(description="Send a private message to another player in a Mafia game")
    async def pm(interaction, target: T.Union[disnake.User, disnake.Member], message: str) -> None:
        interaction: "disnake.ApplicationCommandInteraction" = interaction
        # route the command into the game messenger directly, if we can find a game
        if interaction.channel.type == disnake.ChannelType.public_thread:
            game = GAMES.get(interaction.channel.parent)
        else:
            game = GAMES.get(interaction.channel)
        if game is None or game.messenger is None:
            await interaction.send("Cannot send private message right now", ephemeral=True, delete_after=15.0)
            return
        if game.messenger.external_pm(interaction.user.name, target.name, message):
            # the fact that a private message was sent should be public knowledge
            await interaction.send(f"(To **{target.name}**): {message}", ephemeral=True)
            await interaction.send(f"{interaction.user.name} sent a private message to {target.name}")
        else:
            await interaction.send(f"Unable to send private message to {target.name}", ephemeral=True)

    @bot.slash_command(description="[DEBUG] Disable the Anonymous chat Automod rule")
    async def disable_anon(interaction):
        interaction: "disnake.ApplicationCommandInteraction" = interaction
        if interaction.user.name not in ('chilly mango', 'donbot', 'asiannub'):
            await interaction.send("Unable to use command", ephemeral=True)
        rules = await interaction.guild.fetch_automod_rules()
        for rule in rules:
            if rule.name == "Anonymity":
                break
        else:
            await interaction.send("Unable to find the Automod rule", ephemeral=True)
        await rule.edit(enabled=False)
        await interaction.send("Automod rule disabled", ephemeral=True)

    @bot.slash_command(description="Interact with a Mafia Game")
    async def mafia(interaction, command_input: str):
        """Play Mafia or something"""
        interaction: Interaction = interaction
        command, _, args = command_input.partition(' ')
        bot.user.name = "Mafia Bot"
        #interaction.author.nick = "This is a test nickname"
        # change the username real fast?
        #name_changer = NameChanger(bot.user)
        #await interaction.guild.me.edit(nick='Hello Crier Here')
        #async with name_changer.temporary_name("hello test bot name"):
        #async with name_changer.temporary_name("hello2 electric boogaloo"):
        #    await interaction.send("yeet me into the sun")
        lobby = lobby_manager.get(interaction.guild)
        if command == "test":
            # testing Court anonymity?!
            # add the automod rule and enable it?
            #rule = await interaction.guild.create_automod_rule(
            #    name="Anonymity",
            #    event_type=disnake.AutoModEventType.message_send,
            #    actions=[disnake.AutoModAction(type=disnake.AutoModActionType.block_message)],
            #    trigger_type=disnake.AutoModTriggerType.keyword,
            #    trigger_metadata=disnake.AutoModTriggerMetadata(regex_patterns=["^.*$"]),
            #    enabled=True,
            #    # in prod, exempt the default non-playing server role
            #)
            game = Game({})
            gf = Godfather({})
            game.add_actors(Actor(Player(interaction.user.name), gf, game))
            driver = await ChatDriver.create_with_name(
                game, interaction.channel, "CourtChat"
            )
            CHAT_DRIVERS[interaction.channel] = driver
            driver.start()

#            async for member in interaction.guild.fetch_members():  # replace with live players
#                if member.bot:
#                    continue
#
#                try:
#                    await member.edit(nick="Someone")
#                except Exception as exc:
#                    print(f"Skipping nickname edit for {member.name}")

            await interaction.send("new thread")
            post = await interaction.original_response()
            thread = await interaction.channel.create_thread(name="Court Chat", message=post)
            driver.set_discussion_thread(thread)

            async with thread.typing():
                
                await interaction.send("okee")
                await asyncio.sleep(600.0)

#            try:
#                await rule.delete()
#            except Exception as exc:
#                print(f"Failed to delete AutoModRule: {repr(exc)}")

#            async for member in interaction.guild.fetch_members():  # replace with live players
#                if member.bot:
#                    continue
#                try:
#                    await member.edit(nick=None)
#                except Exception as exc:
#                    print(f"Skipping nickname edit for {member.name}")

        elif command == "mafia-chat":
            await interaction.send("ack", ephemeral=True)
            # open a private thread?
            thread = await interaction.channel.create_thread(name="Mafia Chat", type=disnake.ChannelType.private_thread)
            await thread.add_user(interaction.user)
            await asyncio.sleep(30.0)
            await thread.remove_user(interaction.user)

        elif command == "hover-tip":
            embed = disnake.Embed()
            embed.title = "Testing a Tooltip"
            embed.description = "[(Godfather)](https://www.google.com/ \"HEYAAAAA\")"
            await interaction.send(embed=embed)

        elif command == "print-msg":
            #router.register_message_callback(interaction.channel.name, print_msg)
            await interaction.send("i'm printing messages")
        elif lobby is None or lobby.state in (LobbyState.OPEN, LobbyState.CLOSED):
            await lobby_subparser(interaction.user, interaction, command, args)
        elif lobby.state == LobbyState.STARTED:
            await game_subparser(interaction.user, interaction, command, args)

    bot.run(TOKEN)
    print("Shutdown complete")


if __name__ == "__main__":
    main()
