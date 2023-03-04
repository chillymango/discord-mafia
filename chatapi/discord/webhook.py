"""
FINALLY!

Send messages appearing as other players.
"""
import aiohttp
import disnake
import os

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if TOKEN is None:
    raise OSError("No bot token")

URLS = {
    "Don Bot": "https://discordapp.com/api/webhooks/1081647153623085106/Q2ZwpETtdg59H_6-imzb20qyLL_O2hBftU3YvjbsgXLV5WeGa3l-b3EIYkqs6Wnwdp2T"
}


class WebhookManager:
    """
    Manages Webhooks for user interactions in the Mafia game
    """


async def don_bot_message(username: str, message: str, token: str = TOKEN):
    # TODO: getting pictures in place would be cool
    url = URLS["Don Bot"]
    async with aiohttp.ClientSession() as session:
        webhook = disnake.Webhook.from_url(url, session=session, bot_token=token)
        await webhook.send(message, username=username)
