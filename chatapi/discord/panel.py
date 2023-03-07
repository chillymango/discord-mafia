import asyncio
import typing as T

import disnake
from collections import deque

from chatapi.discord.icache import icache
from chatapi.discord.router import router
from engine.phase import GamePhase
from engine.phase import TurnPhase
from engine.resolver import SequenceEvent
from engine.tribunal import TribunalState

if T.TYPE_CHECKING:
    from chatapi.app.bot import BotUser
    from engine.actor import Actor
    from engine.game import Game
    from engine.player import User


SKIP_DAY = "Skip Day"


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

    REFRESH = True

    def __init__(self, channel: "disnake.TextChannel", debug: bool = False) -> None:
        """
        Classes that inherit from this will also need to specify how to
        rehydrate the view.
        """
        self._debug = debug
        self._channel = channel
        self._content = None
        self._embed = disnake.Embed()
        self._components: T.List[T.Union[disnake.ui.action_row.ActionRow, disnake.Component]] = list()
        self._instances: T.Deque[disnake.Message] = deque()

        # keep track of whether this was active on the previous call
        # typical logic for when to issue vs when to edit is whether
        # there was a rising edge
        # we initialize with a single `False` so a rising edge can be detected
        # on the first turn if appropriate
        self._active_history: T.List[bool] = [False]

        self._prev_pub: T.Dict[str, T.Any] = dict()

        self.initialize()
        self.setup_router()

    def setup_router(self) -> None:
        """
        Child classes must implement this to handle any buttons + selects they may expose
        """

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

    def should_issue(self) -> bool:
        """
        Return True if a new message should be issued, False if not.

        Defaults to True so that we always issue a new message,
        but subclasses should implement this as needed.
        """
        # detect rising edge
        if self._active_history[-1] and not self._active_history[-2]:
            return True
        return False

    def should_delete(self) -> bool:
        """
        In general this should be False, but may be useful to disable stale interactions
        for input panels in particular.
        """
        return False

    def is_active(self) -> bool:
        """
        We default to panels being inactive (not shown).
        """
        return False

    def data_repr(self) -> T.Dict:
        """
        Get the rehydrated output as a recursed dictionary. No Discord objects please!
        """
        components = []
        for c in self._components:
            if isinstance(c, disnake.ui.action_row.ActionRow):
                components.append(c.to_component_dict())
            elif isinstance(c, disnake.Component):
                components.append(c.to_dict())
        return dict(
            content=self._content,
            embed=self._embed.to_dict() if self._embed else None,
            components=components,
        )

    async def drive(self) -> None:
        """
        Update the view

        We shouldn't remove old messages. Just edit old ones if needed.
        """
        self._active_history.append(self.is_active())

        # don't update if the panel isn't active
        if not self.is_active():
            if self.should_delete():
                await self.delete()
            return
        self.update()
        # do not publish if there's no change
        if self.data_repr() == self._prev_pub:
            return
        self._prev_pub = self.data_repr()
        await self.publish()

    async def publish(self) -> None:
        """
        Public vs private panel probably need to implement this differently.

        Default to public panel (implemented here)
        """
        if self.should_issue() or not self._instances:
            self._instances.append(await self._channel.send(**self.rehydrate()))
        else:
            if self.REFRESH:
                await self._instances[-1].edit(**self.rehydrate())
            else:
                try:
                    await self._instances.pop().delete()
                except Exception:
                    print(f"Failed to delete old instance of panel {self.__class__.__name__}")
                self._instances.append(await self._channel.send(**self.rehydrate()))

    async def delete(self, idx: int = None) -> None:
        """
        Delete messages. By default will delete all instances.
        """
        if idx is None:
            await asyncio.gather(*[msg.delete() for msg in self._instances])
            return
        await self._instances[idx].delete()
        self._instances = []


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
        self._closed = False

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

    async def close(self) -> None:
        """
        Show that the game has started and that the lobby is closed.
        """
        self._closed = True
        self.update()
        await self.publish()

    def update(self) -> None:
        if self._closed:
            # remove all buttons
            self._components = []
            self._embed.description = "Game has started. Lobby is **closed**."
            return

        self._embed.clear_fields()
        for idx, user in enumerate(self._users):
            self._embed.add_field(name=f"**Player {idx + 1}**", value=user.name, inline=False)

    def is_active(self) -> bool:
        """
        Lobby is always active until deleted
        """
        return True


class GamePanel(Panel):

    def __init__(self, game: "Game", channel: "disnake.TextChannel", debug: bool = False) -> None:
        self._game = game
        super().__init__(channel, debug=debug)


class PublicGamePanel(GamePanel):
    """
    These only need the game to be specified.

    These generally don't require any input.
    """

    def should_delete(self) -> bool:
        # this just a test, what happens?
        return True


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

        self._interact_request_embed = disnake.Embed()
        self._interact_request_embed.title = "Setup Incomplete"
        self._interact_request_embed.description = "Please click the button below to finish setup"
        self._interact_request_row = disnake.ui.ActionRow()
        self._interact_request_row.add_button(style=disnake.ButtonStyle.primary, label="Complete")

        # cache the previous interaction. When we need to "edit", we only edit the previous issue
        # if it exists. Following the original panel logic, we will always issue if this is None.
        self._previous_interaction: disnake.InteractionMessage = None
        super().__init__(game, channel, debug=debug)
        self.setup_message_collector()

    @property
    def author(self) -> str:
        """
        This is visible at the very top of the embed typically, and should
        be used to uniquely identify all messages belonging to this panel.
        """
        return "TODO: fill in"

    def should_delete(self) -> bool:
        """
        Delete stale interaction panels to avoid old information from being made available
        """
        if len(self._active_history) == 1:
            return False
        return self._active_history[-1] is False and self._active_history[-2] is True

    def setup_message_collector(self) -> None:
        """
        By default we listen to all sent messages from our bot account and cache them
        as message instances. That way we know which messages to delete.
        """
        router.register_message_callback(self._channel.name, self.on_message)

    async def on_message(self, message: "disnake.Message") -> None:
        """
        fuck lol how do i check that it originated from our request??
        """
        if not message.author.bot:
            return
        if message.interaction is not None and message.interaction.user is not self._actor.player.user:
            return

        # how do we know it was sent from *THIS* panel?
        if not message.embeds:
            return
        if not message.embeds[0].author.name == self.author:
            return
        self._instances.append(message)

    async def maybe_get_interaction_from_cache(self, user: "disnake.User") -> T.Optional[disnake.Interaction]:
        """
        Try to get an interaction from cache.
        """
        ia = icache.get(user)
        if ia is None:
            print(f"No interaction for {user.name}, requesting a new one")
            await self._channel.send(
                embed=self._interact_request_embed,
                components=[self._interact_request_row]
            )
        return ia

    async def publish(self) -> None:
        """
        Private panels always drive into ephemeral messages. These should pull
        from the interaction cache if possible. If there isn't an interaction cache messages,
        we should prompt the user to interact with a message in the game channel.

        In basically every case, we should get an updated interaction (cached updated too).
        This means that if we just edit the original interaction, we can perform the
        edit functionality. HOLY SHIT LETS DO IT

        TODO: this approach drops the first message if we encounter issues, a way to re-drive
        messages would be good. A queued approach would probably be ideal.
        """
        # we don't support the ability to "edit" previous interactions
        # so we always just send a new one i guess
        # TODO: is there some way we could *not* do this? the game UI might be perfect if
        # we could dodge this
        ia = await self.maybe_get_interaction_from_cache(self._actor.player.user)
        if ia is None:
            return

        if not self.should_issue():
            try:
                self._previous_interaction = await ia.edit_original_message(**self.rehydrate())
                return
            except:
                print(f"Failed to edit {self.__class__.__name__} for {self._actor.name}")
        try:
            await ia.send(**self.rehydrate(), ephemeral=True)
        except Exception as exc:
            print(repr(exc))
            print(f"Failed to drive {self.__class__.__name__} for {self._actor.name}")

    async def delete(self, idx: int = None) -> None:
        """
        We cannot delete old interactions, so the best we can do (aside from telling players
        to dismiss them) is to edit the message to be blank...

        TODO: maybe add more granularity
        """
        print('deleting panels')
        ia = icache.get(self._actor.player.user)
        
        for msg in self._instances:
            try:
                await ia.followup.delete_message(msg.id)
            except Exception as exc:
                print(repr(exc))

    async def drive(self) -> None:
        """
        Update the view.

        Do not send updates if the player is dead

        We shouldn't remove old messages. Just edit old ones if needed.
        """
        if not self._actor.is_alive:
            return
        await super().drive()


class GraveyardPanel(PublicGamePanel):
    """
    A message that represents the current state of the Graveyard.

    TODO: maybe it's better to just send this on request

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
        self._embed.description = "A list of players that have been eliminated from the game will be below."
        self._embed.clear_fields()

    def is_active(self) -> bool:
        return self._game.game_phase == GamePhase.IN_PROGRESS and (
            self._game.turn_phase == TurnPhase.DAYLIGHT or
            self._game.turn_phase == TurnPhase.NIGHT
        )

    async def publish(self) -> None:
        """
        If graveyard is empty do not publish a message output
        """
        if not self._game.graveyard:
            return
        await super().publish()

    def update(self) -> None:
        """
        Look at game's tombstones and update the fields
        """
        self._embed.clear_fields()
        for tombstone in self._game.graveyard:
            self._embed.add_field(
                name=f"**{tombstone.actor.name} - {tombstone.actor.role.name}**",
                value=f"{tombstone.turn_phase.name.capitalize()} {tombstone.turn_number}. "
                      f"{tombstone.epitaph}",
                inline=False,
            )


class DayPanel(PrivateGamePanel):
    """
    A message that represents a player's possible day actions.
    """

    @property
    def author(self) -> str:
        return f"{self._actor.name} Daytime"

    @property
    def day_target_id(self) -> str:
        return f"day_target_{self._actor.name}"

    @property
    def has_valid_day_action(self) -> bool:
        return self._actor.has_day_action and self._actor.has_ability_uses

    def is_active(self) -> bool:
        return self._game.game_phase == GamePhase.IN_PROGRESS and (
            self._game.turn_phase == TurnPhase.DAYLIGHT
        )

    def setup_router(self) -> None:
        router.register_string_custom_callback(self.day_target_id, self.update_day_target)

    async def update_day_target(self, interaction: "disnake.Interaction") -> None:
        name = interaction.data['values'][0]
        actor = self._game.get_actor_by_name(name)
        if actor is None:
            self._actor.choose_targets()
            await interaction.response.defer()
        else:
            # if action is instant (it often is), execute immediately
            self._actor.choose_targets(actor)

            # if there are any instant actions, do them immediately
            for action in self._actor.role.day_actions():
                if action.instant():
                    event = SequenceEvent(action(), self._actor)
                    event.execute()

            await interaction.response.defer()

    def _update_embed(self) -> None:
        self._embed.title = self._actor.role.name
        self._embed.description = \
            f"You are {'the' if self._actor.role.unique() else 'a'} **{self._actor.role.name}**.\n\n" \
            f"**Action**: {self._actor.role.day_action_description()}\n"
        # TODO: add statuses, like:
        #   * gov reveal
        #   * blackmailed / 49'd
        self._embed.set_author(name=self.author)

    def initialize(self) -> None:
        self._update_embed()
        self._target_row = disnake.ui.ActionRow()
        self._target_row.add_string_select(
            custom_id=self.day_target_id,
            placeholder="Day Target",
            options=["(No Target)"]
        )
        self._target_row_select = self._target_row[0]

    def _update_valid_targets(self) -> None:
        valid_targets = self._actor.get_target_options(as_str=True)
        valid_targets.insert(0, "(No Target)")

        # listing by name should be fine
        if self._actor.has_day_action and self._actor.has_ability_uses:
            self._target_row_select.options = [disnake.SelectOption(label=x) for x in valid_targets]

    def _update_rows(self) -> None:
        """
        If player has a night action, present a targeting row.

        If player has no night action, don't present anything.
        """
        self._components = []
        if self.has_valid_day_action:
            self._components.append(self._target_row_select)

    def update(self):
        """
        Update day action targets
        """
        self._update_embed()
        self._update_valid_targets()
        self._update_rows()


class TribunalPanel(PublicGamePanel):
    """
    A message that represents the current state of the Tribunal.
    """

    @property
    def author(self) -> None:
        return "Trial Votes Here"

    def is_active(self) -> bool:
        return self._game.game_phase == GamePhase.IN_PROGRESS and (
            self._game.turn_phase == TurnPhase.DAYLIGHT
        )

    @property
    def lynch_vote_yes_id(self) -> str:
        return f"lynch_vote_yes"

    @property
    def lynch_vote_no_id(self) -> str:
        return f"lynch_vote_no"

    @property
    def lynch_vote_abs_id(self) -> str:
        return f"lynch_vote_abs"

    @property
    def trial_vote_id(self) -> str:
        return f"trial_vote"

    def initialize(self) -> None:
        # keep track of row height
        # this is so that we do not shrink the box size too quickly
        # for now at least we'll actually just make it so the row height cannot shrink
        # after it's been expanded. we pad the top i guess? see which one feels better
        self._row_height = 0

        self._update_embed()
        self._trial_vote_row = disnake.ui.ActionRow()
        self._trial_vote_row.add_string_select(
            custom_id=self.trial_vote_id,
            placeholder="Trial Vote",
            options=["(No Target)"]
        )
        self._trial_row_select = self._trial_vote_row[0]

        self._lynch_vote_row = disnake.ui.ActionRow()
        self._lynch_vote_row.add_button(
            custom_id=f"{self.lynch_vote_yes_id}",
            label="Yes"
        )
        self._lynch_vote_row.add_button(
            custom_id=f"{self.lynch_vote_no_id}",
            label="No"
        )
        self._lynch_vote_row.add_button(
            custom_id=f"{self.lynch_vote_abs_id}",
            label="Abstain"
        )

    def setup_router(self) -> None:
        router.register_string_custom_callback(self.trial_vote_id, self.update_trial_vote)
        router.register_button_custom_callback(self.lynch_vote_yes_id, self.lynch_vote_yes)
        router.register_button_custom_callback(self.lynch_vote_no_id, self.lynch_vote_no)
        router.register_button_custom_callback(self.lynch_vote_abs_id, self.lynch_vote_abstain)

    def _update_embed(self) -> None:
        self._embed.title = f"Tribunal"
        self._embed.description = self._game.tribunal.get_state_description()
        self._embed.set_author(name=self.author)

    def _update_targets(self) -> None:
        valid_targets = [x.name for x in self._game.get_live_actors()]
        valid_targets.insert(0, "(No Target)")
        self._trial_row_select.options = [disnake.SelectOption(label=x) for x in valid_targets]

    def _update_rows(self) -> None:
        if self._game.tribunal.state == TribunalState.TRIAL_VOTE:
            self._components = [self._trial_vote_row]
            return
        if self._game.tribunal.state == TribunalState.LYNCH_VOTE:
            self._components = [self._lynch_vote_row]
            return
        self._components = []

    def update(self) -> None:
        self._update_embed()
        self._update_targets()
        self._update_rows()

    async def update_trial_vote(self, interaction: "disnake.Interaction") -> None:
        """
        Update target trial vote
        """
        name = interaction.data['values'][0]
        actor = self._game.get_actor_by_name(interaction.user.name)
        if name == SKIP_DAY:
            self._game.tribunal.submit_skip_vote(actor, actor)
        else:
            target = self._game.get_actor_by_name(name)
            self._game.tribunal.submit_trial_vote(actor, target)

        # delegate handling of response to Tribunal
        await interaction.response.defer()

    async def handle_lynch_vote(self, interaction: "disnake.Interaction", vote: T.Optional[bool]) -> None:
        name = interaction.user.name
        actor = self._game.get_actor_by_name(name)
        self._game.tribunal.submit_lynch_vote(actor, vote)
        # we send an interaction here since the panel is public
        await interaction.response.defer()

    async def lynch_vote_yes(self, interaction: "disnake.Interaction") -> None:
        await self.handle_lynch_vote(interaction, True)

    async def lynch_vote_no(self, interaction: "disnake.Interaction") -> None:
        await self.handle_lynch_vote(interaction, False)

    async def lynch_vote_abstain(self, interaction: "disnake.Interaction") -> None:
        await self.handle_lynch_vote(interaction, None)


class NightPanel(PrivateGamePanel):
    """
    A message that represents a player's possible night actions.
    """

    @property
    def author(self) -> str:
        return f"{self._actor.name} Nighttime"

    def is_active(self) -> bool:
        return self._game.game_phase == GamePhase.IN_PROGRESS and (
            self._game.turn_phase == TurnPhase.NIGHT
        )

    @property
    def night_target_id(self) -> str:
        return f"night_target_{self._actor.name}"

    @property
    def wear_vest_id(self) -> str:
        return f"wear_vest_{self._actor.name.replace(' ', '_')}"

    @property
    def remove_vest_id(self) -> str:
        return f"remove_vest_{self._actor.name.replace(' ', '_')}"

    def setup_router(self) -> None:
        router.register_string_custom_callback(self.night_target_id, self.update_night_target)
        router.register_button_custom_callback(self.wear_vest_id, self.wear_vest)
        router.register_button_custom_callback(self.remove_vest_id, self.remove_vest)

    def _update_embed(self) -> None:
        self._embed.title = self._actor.role.name
        self._embed.description = \
            f"You are {'the' if self._actor.role.unique() else 'a'} **{self._actor.role.name}**.\n\n" \
            f"**Action**: {self._actor.role.night_action_description()}"
        self._embed.set_author(name=self.author)
        if self._actor.vests:
            self._embed.description += f"You have {self._actor.vests} bulletproof vests remaining.\n"
            if self._actor._vest_active:
                self._embed.description += f"You are wearing a bulletproof vest.\n"
            else:
                self._embed.description += f"You are not wearing a bulletproof vest.\n"

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

    @property
    def has_valid_night_action(self) -> bool:
        return self._actor.has_night_action and self._actor.has_ability_uses

    def _update_valid_targets(self) -> None:
        valid_targets = self._actor.get_target_options(as_str=True)
        valid_targets.insert(0, "(No Target)")

        # listing by name should be fine
        if self.has_valid_night_action:
            self._target_row_select.options = [disnake.SelectOption(label=x) for x in valid_targets]

    def _update_rows(self) -> None:
        """
        If player has a night action, present a targeting row.

        If player has no night action, don't present anything.
        """
        self._components = []
        if self.has_valid_night_action:
            self._components.append(self._target_row_select)
        if self._actor.vests:
            self._components.append(self._use_vest_row)

    def update(self):
        """
        Update night action targets
        """
        self._update_embed()
        self._update_valid_targets()
        self._update_rows()

    async def update_night_target(self, interaction: "disnake.Interaction") -> None:
        name = interaction.data['values'][0]
        actor = self._game.get_actor_by_name(name)
        if actor is None:
            self._actor.choose_targets()
            await interaction.response.defer()
        else:
            self._actor.choose_targets(actor)
            await interaction.response.defer()

    async def wear_vest(self, interaction: "disnake.Interaction") -> None:
        actor = self._game.get_actor_by_name(interaction.user.name)
        if actor is None:
            await interaction.send(f"Invalid user, cannot wear vest")
        else:
            self._actor.put_on_vest()
            await interaction.response.defer()

    async def remove_vest(self, interaction: "disnake.Interaction") -> None:
        actor = self._game.get_actor_by_name(interaction.user.name)
        if actor is None:
            await interaction.send(f"Invalid user, cannot wear vest")
        else:
            self._actor.take_off_vest()
            await interaction.response.defer()


class WelcomePanel(PrivateGamePanel):
    """
    This should be shown when the game first starts.

    We use the fact that it should only update on rising edge combined
    with the fact that the data_repr should never change to ensure that
    the message is only sent and updated once.

    It will:
        * tag the player by nickname
        * inform the player as to their role
        * describe the rules regarding their role
        * TODO: add setup-specific info
    """

    def is_active(self) -> bool:
        return True

    def update_embed(self) -> None:
        role = self._actor.role
        self._embed.description = f"You are a **{role.name}**.\n\n" \
            f"**Role Description**:\n" \
            f"{role.role_description()}\n\n" \
            f"**Affiliation**:\n" \
            f"{role.affiliation_description()}\n\n" \
            f"**Win Condition**:\n" \
            f"{role.win_condition().description()}\n\n" \
            f"**Day Action**:\n{role.day_action_description()}\n\n" \
            f"**Night Action**:\n{role.night_action_description()}\n\n"

    def initialize(self) -> None:
        self._embed = disnake.Embed()
        self._embed.title = "**MAFIA 3.0 - Welcome!**"
        self.update_embed()
        # TODO: add a help button


class JailPanel(PrivateGamePanel):
    """
    This should be shown to the Jailor and allow them to choose to execute
    their target if they have one in jail.
    """
