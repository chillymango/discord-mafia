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

    @property
    def keys(self) -> T.Iterator:
        return self._cache.keys

    @property
    def values(self) -> T.Iterator:
        return self._cache.values

    @property
    def items(self) -> T.Iterator:
        return self._cache.items

    async def update_with_interaction(self, interaction) -> None:
        interaction: "disnake.Interaction" = interaction
        self._cache[interaction.user] = interaction


# singleton object
icache = InteractionCache()
