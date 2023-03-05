import asyncio
import typing as T

import disnake
from collections import deque

from chatapi.discord.icache import icache
from chatapi.discord.router import router

if T.TYPE_CHECKING:
    from chatapi.app.bot import BotUser
    from engine.actor import Actor
    from engine.game import Game
    from engine.player import User


class Panel:
    """
    This should represent a Discord input or output panel.

    In general the state of this panel may change, and we
    either need to edit the original representation
    in Discord, or we need to send a new message.

    In general this will just wrap the components required
    to issue a message, as well as keep track of the actual
    message itself so that `edit` or `delete` can be issued.

    This should also specify whether it's a private or public
    panel.
    """

    def __init__(self, channel: "disnake.TextChannel", debug: bool = False) -> None:
        """
        Classes that inherit from this will also need to specify how to
        rehydrate the view.
        """
        self._debug = debug
        self._channel = channel
        self._content = None
        self._embed = disnake.Embed()
        self._components: T.List[disnake.Component] = list()
        self._instances: T.Deque[disnake.Message] = deque()
        self.initialize()

    def initialize(self) -> None:
        """
        Subclasses should implement this
        """

    def update(self):
        """
        Update view. This can be called standalone but is typically
        called as part of drive.

        Subclasses should implement this
        """

    def rehydrate(self) -> T.Dict[str, T.Any]:
        """
        Re-generate the send args
        """
        return dict(
            content=self._content,
            embed=self._embed,
            components=self._components,
        )

    async def drive(self, issue: bool = True) -> None:
        """
        Update the view

        We shouldn't remove old messages. Just edit old ones if needed.
        """
        self.update()
        if issue or not self._instances:
            self._instances.append(await self._channel.send(**self.rehydrate()))
        else:
            await self._instances[-1].edit(**self.rehydrate())


class LobbyPanel(Panel):
    """
    A message that represents the Lobby.
    """

    TITLE = "Mafia Lobby"
    DESCRIPTION = "Need 15 players to start"

    def __init__(self, channel: "disnake.TextChannel", users: T.List[T.Union["User", "BotUser"]], debug: bool = False) -> None:
        super().__init__(channel, debug=debug)
        # lets gooo pass by reference
        self._users = users

    def initialize(self) -> None:
        """
        The Lobby should just be a header followed by
        a list of all currently enrolled players.

        Players should be indicated as either human or bot
        depending on where they came from.
        """
        self._embed.title = self.TITLE
        self._embed.description = self.DESCRIPTION

        # a row for join/leave lobby interaction
        join_leave_row = disnake.ui.ActionRow()

        # TODO: additionally partition this by guild ID or something
        join_leave_row.add_button(style=disnake.ButtonStyle.primary, label="Join Game", custom_id="join")
        join_leave_row.add_button(style=disnake.ButtonStyle.grey, label="Leave Game", custom_id="leave")

        # a row for start lobby interaction maybe?
        start_end_row = disnake.ui.ActionRow()
        start_end_row.add_button(style=disnake.ButtonStyle.green, label="Start Game", custom_id="start")
        start_end_row.add_button(style=disnake.ButtonStyle.red, label="Close Lobby", custom_id="close")

        rows = [join_leave_row, start_end_row]
        if self._debug:
            debug_row = disnake.ui.ActionRow()
            debug_row.add_button(style=disnake.ButtonStyle.danger, label="Add Bot", custom_id="add_bot")
            debug_row.add_button(style=disnake.ButtonStyle.danger, label="Remove Bot", custom_id="remove_bot")
            rows.append(debug_row)
        self._components = rows[:]

    def update(self) -> None:
        self._embed.clear_fields()
        for idx, user in enumerate(self._users):
            self._embed.add_field(name=f"**Player {idx + 1}**", value=user.name, inline=False)

    async def delete(self, idx: int = None) -> None:
        """
        Delete messages. By default will delete all instances.
        """
        if idx is None:
            print('trying to delete all messages?')
            await asyncio.gather(*[msg.delete() for msg in self._instances])
            return
        await self._instances[idx].delete()


class GamePanel(Panel):

    def __init__(self, game: "Game", channel: "disnake.TextChannel", debug: bool = False) -> None:
        self._game = game
        super().__init__(channel, debug=debug)


class PublicGamePanel(GamePanel):
    """
    These only need the game to be specified.

    These generally don't require any input.
    """


class PrivateGamePanel(GamePanel):
    """
    These need the actor to be specified.

    These should only exist for game players.
    """

    def __init__(
        self,
        actor: "Actor",
        game: "Game",
        channel: "disnake.TextChannel",
        debug: bool = False
    ) -> None:
        self._actor = actor
        if not self._actor.player.is_human:
            raise ValueError(f"Player {actor.name} is not a human")
        super().__init__(game, channel, debug=debug)


class GraveyardPanel(PublicGamePanel):
    """
    A message that represents the current state of the Graveyard.

    This should be a public message that's updated:
    * during daybreak (send new)
    * during dusk (send new)
    * if a daytime kill happens (i.e Constable -- update last)
    """

    def initialize(self) -> None:
        """
        Generally initialize to empty.
        Can add fields with descriptions as we get them.
        """
        self._embed.title = "Graveyard"
        self._embed.clear_fields()

    def update(self) -> None:
        """
        Look at game's tombstones and update the fields
        """
        self._embed.clear_fields()
        for tombstone in self._game.graveyard:
            self._embed.add_field(
                name=f"**{tombstone.actor.name} - {tombstone.actor.role.name}**",
                value=f"{tombstone.turn_phase.name.capitalize()} {tombstone.turn_number}. "
                      f"{tombstone.epitaph}"
            )


class DayPanel(PrivateGamePanel):
    """
    A message that represents a player's possible day actions.
    """

    @property
    def day_target_id(self) -> str:
        return f"day_target_{self._actor.name}"

    def _update_embed(self) -> None:
        self._embed.title = f"Day {self._game.turn_number}"
        self._embed.description = \
            f"You are a **{self._actor.role.name}**.\n\n" \
            f"**Action**: {self._actor.role.day_action_description()}"

    def initialize(self) -> None:
        self._update_embed()
        self._target_row = disnake.ui.ActionRow()
        self._target_row.add_string_select(
            custom_id=self.day_target_id,
            placeholder="Day Target",
            options=["(No Target"]
        )
        self._target_row_select = self._target_row[0]

    def _update_valid_targets(self) -> None:
        valid_targets = self._actor.get_target_options(as_str=True)
        valid_targets.insert(0, "(No Target)")

        # listing by name should be fine
        if self._actor.has_day_action and self._actor.has_ability_uses:
            self._target_row_select.options = [disnake.SelectOption(label=x) for x in valid_targets]

    def update(self):
        """
        Update day action targets
        """
        self._update_embed()
        self._update_valid_targets()


class TribunalPanel(PublicGamePanel):
    """
    A message that represents the current state of the Tribunal.
    """


class NightPanel(PrivateGamePanel):
    """
    A message that represents a player's possible night actions.
    """

    @property
    def night_target_id(self) -> str:
        return f"night_target_{self._actor.name}"

    @property
    def wear_vest_id(self) -> str:
        return f"wear_vest_{self._actor.name.replace(' ', '_')}"

    @property
    def remove_vest_id(self) -> str:
        return f"remove_vest_{self._actor.name.replace(' ', '_')}"

    def _update_embed(self) -> None:
        self._embed.title = f"Night {self._game.turn_number}"
        self._embed.description = \
            f"You are a **{self._actor.role.name}**.\n\n" \
            f"**Action**: {self._actor.role.night_action_description()}"
        if self._actor.vests:
            self._embed.description += f"You have {self._actor.vests} bulletproof vests remaining."

    def initialize(self) -> None:
        self._update_embed()
        self._target_row = disnake.ui.ActionRow()
        self._target_row.add_string_select(
            custom_id=self.night_target_id,
            placeholder="Night Target",
            options=["(No Target"]
        )
        self._target_row_select = self._target_row[0]

        self._use_vest_row = disnake.ui.ActionRow()
        self._use_vest_row.add_button(
            custom_id=self.wear_vest_id,
            label="Wear Vest",
        )
        self._use_vest_row.add_button(
            custom_id=self.remove_vest_id,
            label="Remove Vest",
        )

        # button callbacks
        self._

    def _update_valid_targets(self) -> None:
        valid_targets = self._actor.get_target_options(as_str=True)
        valid_targets.insert(0, "(No Target)")

        # listing by name should be fine
        if self._actor.has_night_action and self._actor.has_ability_uses:
            self._target_row_select.options = [disnake.SelectOption(label=x) for x in valid_targets]

    def update(self):
        """
        Update night action targets
        """
        self._update_embed()
        self._update_valid_targets()
