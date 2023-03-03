import typing as T
import disnake
from engine.message import MessageDriver

if T.TYPE_CHECKING:
    from chatapi.discord.input_panel import InputController
    from engine.message import Message
    from engine.player import Player


class DiscordDriver(MessageDriver):
    """
    Drives Discord messages
    """

    def __init__(
        self,
        pub_channel: "disnake.TextChannel",
        interaction_cache: T.Dict["disnake.User", "disnake.Interaction"],
        controller: "InputController"
    ) -> None:
        self._pub_channel = pub_channel
        self._interaction_cache = interaction_cache
        self._controller = controller

    async def public_publish(self, message: "Message") -> None:
        await self._pub_channel.send(message)

    async def private_publish(self, player: "Player", message: "Message") -> None:
        # TODO: is there a better way to do it than manually checking?
        # we can't cache it locally since the original dictionary is prone to changing
        # we could maybe store it differently in both cases
        # ... or actually Player should just contain a reference to User
        for user, interaction in self._interaction_cache.items():
            if user.name == player.name:
                break
        else:
            print(f"No interaction found for {player.name}. Dropping message: {message.message}")
            return None

        # TODO: i think this is a bug with disnake but I might just be sleepy
        try:
            await interaction.send(content=message.message, ephemeral=True)
        except:
            await interaction.followup.send(content=message.message, ephemeral=True)

    async def edit_last_private(self, player: "Player", **kwargs: T.Any) -> None:
        """
        Edit the previously issued private message sent to a player
        """
        for user, interaction in self._interaction_cache.items():
            if user.name == player.name:
                break
        else:
            return None
        try:
            await interaction.edit_original_response(**kwargs)
        except:
            print('Followup update')
            await interaction.followup.edit(**kwargs)
