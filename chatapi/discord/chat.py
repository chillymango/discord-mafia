"""
Shared global storage?

Since the Bot needs access to ChatDrivers when it executes slash commands
and we seem to not be able to add them post-init
"""
import typing as T

if T.TYPE_CHECKING:
    import disnake
    from chatapi.discord.driver import ChatDriver


# TODO: different keying is probably wanted
# currently we key by top-level channel since each game should have a single
# channel for bulletin that we can use
CHAT_DRIVERS: T.Dict["disnake.TextChannel", "ChatDriver"] = dict()
