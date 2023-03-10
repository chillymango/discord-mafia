"""
Channel Manager

Singleton object that manages channels. The bot must delete all
created channels when it exits so we use this object to manage that.
"""
import asyncio
import typing as T
import disnake


class ChannelManager:
    
    def __init__(self) -> None:
        self._channels: T.Dict[str, "disnake.TextChannel"] = dict()
        self._preserve: T.Dict["disnake.TextChannel", bool] = dict()

    async def create_channel(self, guild: "disnake.Guild", name: str, **kwargs) -> disnake.TextChannel:
        """
        If the channel by this name already exists, just return it.
        """
        if name not in self._channels:
            self._channels[name] = await guild.create_text_channel(name=name, **kwargs)
        return self._channels[name]

    def get_channel(self, name: str) -> T.Optional["disnake.TextChannel"]:
        """
        Return a channel if it exists.
        """
        return self._channels.get(name)

    def mark_to_preserve(self, channel: "disnake.TextChannel") -> None:
        self._preserve[channel] = True

    def _remove_if_exists(self, channel: "disnake.TextChannel") -> bool:
        return self._channels.pop(channel.name, None) is not None

    async def maybe_delete_channel(self, channel: T.Optional["disnake.TextChannel"] = None, channel_name: str = None) -> None:
        """
        Specify one of `channel` or `channel_name` as input to delete it.

        Delete the channel if we have knowledge of it.
        """
        if channel is not None and channel_name:
            raise ValueError("Cannot specify both a channel and a channel_name")

        if channel:
            await channel.delete()
            self._remove_if_exists(channel)
            return

        if channel_name:
            ch = self.get_channel(channel_name)
            if ch is None:
                return
            await self.maybe_delete_channel(ch)

        raise ValueError("No `channel` or `channel_name` specified")

    async def shutdown(self) -> None:
        """
        Delete all channels

        TODO: i don't think we need to do this actually...
        maybe just rename them on game finish?
        """
        to_delete: T.List["disnake.TextChannel"] = []
        for ch in self._channels.values():
            if not self._preserve.get(ch, False):
                to_delete.append(ch)
        await asyncio.gather(*[ch.delete() for ch in to_delete])


channel_manager: ChannelManager = ChannelManager()
