"""
Create some permission groups for the game
"""
import typing as T
import disnake

LIVE_PLAYER = "Live Player"
MAFIA_LIVE = "Mafia Live"


class PermissionsManager:
    """
    We probably want one per guild
    """

    def __init__(self, guild: "disnake.Guild") -> None:
        self._guild = guild
        self._roles = dict()

    async def setup_roles(self) -> T.Dict[str, "disnake.Role"]:
        # Live Player
        # A Live Player is alive and attached to a game of Mafia.
        # When players in Mafia die, they are removed from this role.

        self._roles[LIVE_PLAYER] = await self._guild.create_role(name=LIVE_PLAYER)
    
        # Mafia Player
        # A Mafia Player is a live player with the Mafia affiliation.
        # This should give them access to the Mafia night-time chat.
        self._roles[MAFIA_LIVE] = await self._guild.create_role(name=MAFIA_LIVE)

        # TODO: JAIL ROLES!!!

        # add all roles
        ALL_ROLES.update(self._roles.values())

        return self._roles


# during cleanup we want to delete every single role we've added
ALL_ROLES: T.Set["disnake.Role"] = set()
