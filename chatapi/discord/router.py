"""
Button Click Input Router
"""
import asyncio
import typing as T
from cachetools import TTLCache
from collections import defaultdict
import disnake


class Subrouter:
    """
    Composite object for Router
    """

    def __init__(self) -> None:
        self._general_callbacks: T.List[T.Coroutine] = list()
        self._custom_id_callbacks: T.Dict[str, T.Coroutine] = dict()
        self._seen_interactions = TTLCache(maxsize=1000, ttl=5)

    def register_general_callback(self, callback: T.Coroutine) -> None:
        if callback not in self._general_callbacks:
            self._general_callbacks.append(callback)

    def unregister_general_callback(self, callback: T.Coroutine) -> None:
        if callback in self._general_callbacks:
            self._general_callbacks.remove(callback)

    def register_custom_callback(self, key: str, callback: T.Coroutine) -> None:
        if key in self._custom_id_callbacks:
            raise KeyError(f"Callback already registered for key {key}")
        self._custom_id_callbacks[key] = callback

    def unregister_custom_callback(self, key: str) -> None:
        if key in self._custom_id_callbacks:
            self._custom_id_callbacks.pop(key)


class Router:

    def __init__(self) -> None:
        self._button_router = Subrouter()
        self._string_router = Subrouter()
        self._modal_router = Subrouter()

        # mapping of channel name to a subrouter for that channel
        self._message_routers: T.Dict[str, Subrouter] = defaultdict(Subrouter)

        self._button_general_callbacks: T.List[T.Coroutine] = list()
        self._button_custom_id_callbacks: T.Dict[str, T.Coroutine] = dict()
        self._string_general_callbacks: T.List[T.Coroutine] = list()
        self._string_custom_id_callbacks: T.Dict[str, T.Coroutine] = dict()
        self._seen_interactions = TTLCache(maxsize=1000, ttl=5)

    def register_button_general_callback(self, callback: T.Coroutine) -> None:
        self._button_router.register_general_callback(callback)

    def unregister_button_general_callback(self, callback: T.Coroutine) -> None:
        self._button_router.unregister_general_callback(callback)

    def register_button_custom_callback(self, key: str, callback: T.Coroutine) -> None:
        self._button_router.register_custom_callback(key, callback)

    def unregister_button_custom_callback(self, key: str) -> None:
        self._button_router.unregister_custom_callback(key)

    def register_string_general_callback(self, callback: T.Coroutine) -> None:
        self._string_router.register_general_callback(callback)

    def unregister_string_general_callback(self, callback: T.Coroutine) -> None:
        self._string_router.unregister_general_callback(callback)

    def register_string_custom_callback(self, key: str, callback: T.Coroutine) -> None:
        self._string_router.register_custom_callback(key, callback)

    def unregister_string_custom_callback(self, key: str) -> None:
        self._string_router.unregister_custom_callback(key)

    def register_message_callback(self, channel: str, callback: T.Coroutine) -> None:
        self._message_routers[channel].register_general_callback(callback)

    def unregister_message_callback(self, channel: str, callback: T.Coroutine) -> None:
        self._message_routers[channel].unregister_general_callback(callback)

    def register_custom_modal_callback(self, custom_id: str, callback: T.Coroutine) -> None:
        self._modal_router.register_custom_callback(custom_id, callback)

    def unregister_custom_modal_callback(self, custom_id: str) -> None:
        self._modal_router.unregister_custom_callback(custom_id)

    def register_general_modal_callback(self, callback: T.Coroutine) -> None:
        self._modal_router.register_general_callback(callback)

    def unregister_general_modal_callback(self, callback: T.Coroutine) -> None:
        self._modal_router.unregister_general_callback(callback)

    async def on_message(self, message: "disnake.Message") -> None:
        router = self._message_routers.get(message.channel.name)
        if router is None:
            return
        # TODO: i don't think it makes sense to support custom_id filters for message
        # interactions but will need to re-evaluate this in the future
        await asyncio.gather(*[gcb(message) for gcb in router._general_callbacks])

    async def on_modal_submit(self, interaction: "disnake.Interaction") -> None:
        await self.on_interact(self._modal_router, interaction)

    async def on_interact(self, router: "Subrouter", interaction: "disnake.Interaction") -> None:
        print(interaction.id)  # debugging, see how often we get duplicates
        if interaction.id in self._seen_interactions:
            # should already be replied
            return

        try:
            await asyncio.gather(*[gcb(interaction) for gcb in router._general_callbacks])
        except Exception as exc:
            print(f"Error executing callback: {repr(exc)}")

        try:
            key: str = interaction.data.custom_id
        except AttributeError:
            print("Warning: could not parse interaction")

        callback = router._custom_id_callbacks.get(key)
        if callback is None:
            print(f"Warning: could not find a callback for key {key}")
            await interaction.send(f"wtf was clicked? {interaction.data.custom_id}")
            return
        await callback(interaction)

    async def on_string_select(self, interaction: "disnake.Interaction") -> None:
        await self.on_interact(self._string_router, interaction)

    async def on_button_click(self, interaction: "disnake.Interaction") -> None:
        await self.on_interact(self._button_router, interaction)


router = Router()
