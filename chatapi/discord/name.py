"""
Manages name status.

We want to change our name when we issue messages as the bot
"""
from contextlib import asynccontextmanager
import asyncio
import typing as T

if T.TYPE_CHECKING:
    import disnake
 

class NameChanger:
    """
    Hopefully this is performant enough to run this game.

    TODO: timing metrics on typical lock acquisition time for name change.
    """
    
    def __init__(self, bot_user: "disnake.ClientUser", name: str = "Mafia Game Bot") -> None:
        self._bot_user = bot_user
        self._true_name = name
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def temporary_name(self, name: str) -> T.Iterator[None]:
        changed = False
        try:
            await self._bot_user.edit(username=name)
            changed = True
            yield
        finally:
            if changed:
                await self._bot_user.edit(username=self._true_name)
