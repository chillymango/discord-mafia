"""
Interaction Cache
"""
import typing as T

if T.TYPE_CHECKING:
    import disnake


class InteractionCache:

    def __init__(self):
        self._cache: T.Dict["disnake.User", "disnake.Interaction"] = dict()

    def get(self, user: "disnake.User") -> T.Optional["disnake.Interaction"]:
        return self._cache.get(user)

    def keys(self) -> T.Iterator:
        return self._cache.keys

    def values(self) -> T.Iterator:
        return self._cache.values

    def items(self) -> T.Iterator:
        return self._cache.items

    async def update_with_interaction(self, interaction) -> None:
        interaction: "disnake.Interaction" = interaction
        self._cache[interaction.user] = interaction


# this is basically a singleton
icache = InteractionCache()
