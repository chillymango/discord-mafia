import os
import typing as T

import disnake
from disnake.ext import commands

from chatapi.disnake.menu import Confirm

if T.TYPE_CHECKING:
    from disnake.ext.commands import Context

TOKEN = 'MTA3OTg1MDUzNjUwMjgyOTEzNg.GokFWW.MrfXK8bZGcJ_wG09yiAKjvVMiXIy-rnOMLU8pI'

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(intents=intents, command_prefix='!')

game = None
players = list()


@bot.command(name='create-lobby')
async def create_lobby(ctx: "Context", channel_name='disnake-mafia-game'):
    global game
    if game is not None:
        ctx.message.channel.send("A lobby already exists by that name")
        return

    game = 'todo'
    await ctx.message.channel.send("Starting a disnake Mafia game")
    guild = ctx.guild
    existing_channel = disnake.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

@bot.command(name='start-game')
async def start_game(ctx: "Context"):
    pass

@bot.command(name="test")
async def join_game(ctx: "Context"):
    emb = disnake.Embed(title=f"Mafia Lobby", description='this is a test')
    disnake.Client.add_view()
    await ctx.send(embed=emb)
    #m = Confirm('You are about to join a Mafia game. Press to confirm.')
    #await m.start(ctx)


bot.run(TOKEN)
