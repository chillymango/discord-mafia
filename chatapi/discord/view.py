"""
This isn't the Discord View
...
Er I mean it is

This is something that's got access to both what's generating the state for the UI as well
as what propagates the changes out to the client.
"""
import asyncio
import typing as T

import disnake

from chatapi.discord.input_panel import InputPanel
from chatapi.discord.input_panel import InputController

if T.TYPE_CHECKING:
    from chatapi.discord.driver import DiscordDriver


class ViewController:

    def __init__(
        self,
        input_controller: InputController,
        driver: "DiscordDriver",
        interaction_cache: T.Dict["disnake.User", "disnake.Interaction"]
    ) -> None:
        self._driver = driver
        self._interaction_cache: T.Dict["disnake.User", "disnake.Interaction"] = interaction_cache
        self._input_controller = input_controller

        self._user_by_name: T.Dict[str, "disnake.User"] = {user.name: user for user in self._interaction_cache}

    @property
    def interaction_cache(self) -> T.Dict["disnake.User", "disnake.Interaction"]:
        return self._interaction_cache

    async def update(self, name: str, edit: bool = False, **kwargs) -> None:
        """
        Whenever the appropriate game state update is issued, this update function should
        modify the game state as needed.

        I'm not sure what cases we'll need as of yet, so for now we'll have whatever's making
        the state changes keep in mind how the View needs to update as well.

        If `edit` is True, it will edit the last known message.
        If `edit` is False, it will send a new message.

        TODO: this is a shitty abstraction
        """
        user = self._user_by_name.get(name)
        if user is None:
            print(f"WARN: (view) no user by name {name}")
            return

        # i'm sure this will never fail right...?
        ia = self._interaction_cache.get(user)
        if ia is None:
            print(f"WARN: (view) no interaction for user {name}")
        
        if edit:
            await ia.edit_original_response(**kwargs)
        else:
            await ia.send(**kwargs)

    async def drive(self, edit: bool = False) -> None:
        """
        This drive is called in response to the game state stepping.

        If `edit` is True, it will edit the last known message it's aware of.
        If `edit` is False, it will send a new message.

        TODO: these should eventually be event-driven
        """
        self._input_controller.drive()
        futures = list()
        for user, interaction in self.interaction_cache.items():
            panel = self._input_controller.get_panel(user)
            to_export = panel.export_to_discord()
            if edit:
                futures.append(interaction.edit_original_response(**to_export))
            else:
                futures.append(interaction.send(**to_export, ephemeral=True))

        try:
            await asyncio.gather(*futures)
        except:
            pass
