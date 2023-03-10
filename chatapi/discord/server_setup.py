"""
Adds roles and perms for a standard server setup

Roles Created:
    * Live Mafia Players
Categories Created:
    * Old-Mafia-Games
    * Current-Mafia-Games
    * Open-Lobbies

TODO: a lot of how we key thigns right now is done by guild and not by channel, and so
    there's probably extra work that'd need to be done to host multiple Mafia games
    simultaneously. The next scaling challenge!
"""
import typing as T

if T.TYPE_CHECKING:
    import disnake


async def do_server_setup(interaction: "disnake.Interaction") -> None:
    """
    Connect as our bot and run everything needed
    """
