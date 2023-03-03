"""
Button Click Input Router
"""
import typing as T
from cachetools import TTLCache
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

    async def on_interact(self, router: "Subrouter", interaction: "disnake.Interaction") -> None:
        print(interaction.id)  # debugging, see how often we get duplicates
        if interaction.id in self._seen_interactions:
            # should already be replied
            return

        for gcb in router._general_callbacks:
            try:
                await gcb(interaction)
            except Exception as exc:
                print(f"Error executing callback: {repr(exc)}")

        try:
            key: str = interaction.data.custom_id
        except AttributeError:
            print("Warning: could not parse button click")

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
