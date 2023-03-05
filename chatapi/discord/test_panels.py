"""
Create a Discord bot that just prints out panels for testing

Buttons aren't expected to work, just check the visuals
"""
import asyncio
import os

from disnake.ext import commands
import disnake

from chatapi.app.bot import BotUser
from chatapi.discord.panel import LobbyPanel
from chatapi.discord.panel import GraveyardPanel
from engine.game import Game
from engine.player import Player

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise OSError("No env var DISCORD_BOT_TOKEN")


class TestBot(commands.Bot):
    def __init__(self):
        intents = disnake.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned_or('/'), intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = TestBot()

@bot.command("lobby_panel")
async def lobby_panel(interaction) -> None:
    # add some bots?
    interaction: "disnake.Interaction" = interaction
    users = []
    for idx in range(15):
        users.append(BotUser(name=f"Bot Player {idx}"))
    panel = LobbyPanel(interaction.channel, users, debug=True)
    await panel.drive()
    await interaction.send("ack", ephemeral=True, delete_after=0.0)


@bot.command("graveyard_panel")
async def graveyard_panel(interaction) -> None:
    # add some bots?
    interaction: "disnake.Interaction" = interaction
    users = []
    for idx in range(15):
        users.append(BotUser(name=f"Bot Player {idx}"))
    g = Game()
    g.add_players(([Player(u) for u in users]))
    panel = GraveyardPanel(g, interaction.channel)
    await panel.drive()
    await interaction.send("hehe", ephemeral=True, delete_after=0.0)


def main() -> None:
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
