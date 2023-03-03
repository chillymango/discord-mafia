"""
Player-facing UI components

Probably need:
    * one for daytime (lynch voting + day powers)
    * one for nighttime (night actions)
"""
import typing as T
import disnake

from engine.affiliation import MAFIA
from engine.affiliation import NEUTRAL
from engine.affiliation import TRIAD
from engine.phase import TurnPhase

if T.TYPE_CHECKING:
    from chatapi.discord.router import Router
    from engine.actor import Actor
    from engine.game import Game
    from engine.role.base import Role


SKIP_DAY = "Skip Day"


class InputPanel:
    """
    Stateful control panel.

    TODO: split this from Discord eventually, but for now using a concrete impl is fine
    """

    def __init__(
        self,
        user: "disnake.User",
        actor: "Actor",
        router: "Router",
        debug: bool = True
    ) -> None:
        self._actor = actor
        self._user = user
        self._router = router
        self._debug = debug

        # make everything just once and cycle them into the above depending on when they're needed
        self._init_singletons()
        self._init_debug()
        self._init_daybreak()
        self._init_daylight()
        self._init_dusk()
        self._init_night()
        self._init_night_sequence()

        self._register_callbacks()

    @property
    def game(self) -> "Game":
        return self._actor.game

    @property
    def role(self) -> "Role":
        return self._actor.role

    @property
    def advance_game_id(self) -> str:
        return "advance_game"

    @property
    def trial_vote_id(self) -> str:
        return f"trial_vote_{self._user.name.replace(' ', '_')}"

    @property
    def lynch_vote_yes_id(self) -> str:
        return f"lynch_vote_yes_{self._user.name.replace(' ', '_')}"

    @property
    def lynch_vote_no_id(self) -> str:
        return f"lynch_vote_no_{self._user.name.replace(' ', '_')}"

    @property
    def lynch_vote_abs_id(self) -> str:
        return f"lynch_vote_abs_{self._user.name.replace(' ', '_')}"

    @property
    def day_target_id(self) -> str:
        return f"day_target_{self._user.name.replace(' ', '_')}"

    @property
    def night_target_id(self) -> str:
        return f"night_target_{self._user.name.replace(' ', '_')}"

    @property
    def wear_vest_id(self) -> str:
        return f"wear_vest_{self._user.name.replace(' ', '_')}"

    @property
    def remove_vest_id(self) -> str:
        return f"remove_vest_{self._user.name.replace(' ', '_')}"

    def _register_callbacks(self) -> None:
        self._router.register_string_custom_callback(self.trial_vote_id, self.update_trial_vote)
        self._router.register_string_custom_callback(self.day_target_id, self.update_day_target)
        self._router.register_string_custom_callback(self.night_target_id, self.update_night_target)
        self._router.register_button_custom_callback(self.lynch_vote_yes_id, self.lynch_vote_yes)
        self._router.register_button_custom_callback(self.lynch_vote_no_id, self.lynch_vote_no)
        self._router.register_button_custom_callback(self.lynch_vote_abs_id, self.lynch_vote_abstain)

    def _init_singletons(self) -> None:
        self._trial_embed: "disnake.Embed" = disnake.Embed(title=f"Trial Vote")
        self._lynch_embed: "disnake.Embed" = disnake.Embed(title=f"Lynch Vote")

        self._trial_vote_row = disnake.ui.ActionRow()
        self._trial_vote_row.add_string_select(
            custom_id=self.trial_vote_id,
            placeholder="Trial Vote",
            options=["(Nobody)"]
        )
        self._trial_vote_view = self._trial_vote_row.children[0]

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

        self._day_target_row = disnake.ui.ActionRow()
        self._day_target_row.add_string_select(
            custom_id=self.trial_vote_id,
            placeholder="Day Target",
            options=["(Nobody)"]
        )
        self._day_target_view = self._day_target_row.children[0]

        self._night_target_row = disnake.ui.ActionRow()
        self._night_target_row.add_string_select(
            custom_id=self.night_target_id,
            placeholder="Night Target",
            options=["(Nobody)"]
        )
        self._night_target_view = self._night_target_row.children[0]

        self._use_vest_row = disnake.ui.ActionRow()
        self._use_vest_row.add_button(
            custom_id=self.wear_vest_id,
            label="Wear Vest",
        )
        self._use_vest_row.add_button(
            custom_id=self.remove_vest_id,
            label="Remove Vest",
        )

    def _init_debug(self) -> None:
        if self._debug:
            debug_row = disnake.ui.ActionRow()
            debug_row.add_button(custom_id=self.advance_game_id, label="Advance")
            self._debug_components = [
                debug_row
            ]

    def _init_daybreak(self) -> None:
        if self.role.affiliation == NEUTRAL:
            header = "You are a Neutral role."
        else:
            header = f"You are a member of the {self.role.affiliation.capitalize()}."

        description = (f"{header}\n{self.role.role_description()}\n\n")

        if self.role.affiliation in (MAFIA, TRIAD):
            # also inform who your teammates are
            teammates = self.game.get_actors_with_affiliation(self.role.affiliation)
            description += "Your teammates are:\n\t" + "\n\t".join(
                [f"{x.name} [{x.role.name}]" for x in teammates]
            ) + "\n"

        self._daybreak_embed: "disnake.Embed" = disnake.Embed(
            title=f"**{self.role.name}**",
            description=description
        )
        self._daybreak_components: T.List["disnake.Component"] = []
        if self._debug:
            self._daybreak_components.extend(self._debug_components)

    def _init_daylight(self) -> None:
        self._daylight_embed: "disnake.Embed" = disnake.Embed(
            title=f"Day {self.game.turn_number}",
        )
        self._daylight_components: T.List["disnake.Component"] = [
            self._trial_vote_row,
        ]
        if self._debug:
            self._daylight_components.extend(self._debug_components)

    def _init_dusk(self) -> None:
        """
        Still allow day target changes here but don't allow any lynching
        """
        self._dusk_embed: "disnake.Embed" = disnake.Embed(
            title=f"Dusk {self.game.turn_number}",
        )
        self._dusk_components: T.List["disnake.Component"] = []
        if self._debug:
            self._dusk_components.extend(self._debug_components)

    def _init_night(self) -> None:
        """
        Allow night targeting
        """
        self._night_embed: "disnake.Embed" = disnake.Embed(
            title=f"Night {self.game.turn_number}"
        )
        self._night_components: T.List["disnake.Component"] = [self._night_target_row]
        if self._debug:
            self._night_components.extend(self._debug_components)

    def _init_night_sequence(self) -> None:
        """
        Generally nothing should be allowed here.

        Just sit back and enjoy the show.
        """
        self._night_sequence_embed: "disnake.Embed" = disnake.Embed(
            title=f"Night {self.game.turn_number} is ending..."
        )
        self._night_sequence_components: T.List["disnake.Component"] = []
        if self._debug:
            self._night_sequence_components.extend(self._debug_components)

    def drive(self) -> None:
        """
        Refresh all embeds and components with game state.

        This will not publish out on its own.
        """
        # update valid targets
        self._update_valid_targets()
        if self.game.turn_phase == TurnPhase.NIGHT_SEQUENCE:
            # update all turn numbers lmao
            self._daybreak_embed.title = f"Daybreak on Day {self.game.turn_number}"
            self._daylight_embed.title = f"Day {self.game.turn_number}"
            self._dusk_embed.title = f"Dusk {self.game.turn_number}"
            self._night_embed.title = f"Night {self.game.turn_number}"
            self._night_sequence_embed.title = f"Night {self.game.turn_number} is ending..."

    def _update_valid_targets(self) -> None:
        valid_targets = self._actor.get_target_options(as_str=True)
        valid_targets.insert(0, "(No Target)")

        # listing by name should be fine
        # only give valid targets if there are ability uses left
        if self._actor.has_day_action and self._actor.has_ability_uses:
            self._day_target_view.options = [disnake.SelectOption(label=x) for x in valid_targets]
        if self._actor.has_night_action and self._actor.has_ability_uses:
            # TODO: i already know this will break on jailor, need to fix
            self._night_target_view.options = [disnake.SelectOption(label=x) for x in valid_targets]

        # update lynch vote targets
        valid_lynch = self._actor.get_lynch_options(as_str=True)
        valid_lynch.insert(0, "(No Lynch)")
        self._trial_vote_view.options = [disnake.SelectOption(label=x) for x in valid_lynch]

    def export_to_discord(self) -> T.Dict[str, T.Any]:
        """
        Feed this as kwargs into a `send` call
        """
        to_export = dict( )
        if self.game.turn_phase == TurnPhase.DAYBREAK:
            to_export = dict(
                embed=self._daybreak_embed,
                components=self._daybreak_components,
            )
        if self.game.turn_phase == TurnPhase.DAYLIGHT:
            components = []
            embed = self._daylight_embed
            if self.game.tribunal.show_trial_vote_view:
                embed = self._trial_embed
                components.append(self._trial_vote_row)
            if self.game.tribunal.show_lynch_vote_view:
                embed = self._lynch_embed
                if not self.game.tribunal._on_trial == self._actor:
                    # if the player is on trial don't let them vote lol
                    components.append(self._lynch_vote_row)
            if self._debug:
                components.extend(self._debug_components)
            to_export = dict(
                embed=embed,
                components=components,
            )
        if self.game.turn_phase == TurnPhase.DUSK:
            to_export = dict(
                embed=self._dusk_embed,
                components=self._dusk_components,
            )
        if self.game.turn_phase == TurnPhase.NIGHT:
            components = self._night_components[:]
            if self._actor.vests > 0:
                components.append(self._use_vest_row)
            to_export = dict(
                embed=self._night_embed,
                components=self._night_components,
            )
        if self.game.turn_phase == TurnPhase.NIGHT_SEQUENCE:
            to_export = dict(
                embed=self._night_sequence_embed,
                components=self._night_sequence_components,
            )

        if not self._actor.is_alive:
            to_export["components"] = []
        return to_export

    def update_embed_labels(self) -> None:
        """
        Check the current turn number and update all embed titles
        """
        self._daybreak_embed.title = f"Daybreak {self.game.turn_number}"
        self._daylight_embed.title = f"Daylight {self.game.turn_number}"
        self._dusk_embed.title = f"Dusk {self.game.turn_number}"
        self._night_embed.title = f"Night {self.game.turn_number}"

    async def update_trial_vote(self, interaction: "disnake.Interaction") -> None:
        """
        Update target lynch vote
        """
        name = interaction.data['values'][0]
        if name == SKIP_DAY:
            self.game.tribunal.submit_skip_vote(self._actor, actor)
        else:
            actor = self.game.get_actor_by_name(name)
            self.game.tribunal.submit_trial_vote(self._actor, actor)
        await interaction.send(f"Updated lynch vote", ephemeral=True, delete_after=0.0)

    async def update_day_target(self, interaction: "disnake.Interaction") -> None:
        name = interaction.data['values'][0]
        actor = self.game.get_actor_by_name(name)
        if actor is None:
            self._actor.choose_targets()
            await interaction.send(f"Cleared day target", ephemeral=True, delete_after=0.0)
        else:
            self._actor.choose_targets(actor)
            await interaction.send(f"Updated day target to {name}", ephemeral=True, delete_after=0.0)

    async def update_night_target(self, interaction: "disnake.Interaction") -> None:
        name = interaction.data['values'][0]
        actor = self.game.get_actor_by_name(name)
        if actor is None:
            self._actor.choose_targets()
            await interaction.send(f"Cleared night target", ephemeral=True, delete_after=0.0)
        else:
            self._actor.choose_targets(actor)
            await interaction.send(f"Updated night target to {name}", ephemeral=True, delete_after=0.0)

    async def handle_lynch_vote(self, interaction: "disnake.Interaction", vote: T.Optional[bool]) -> None:
        name = interaction.user.name
        actor = self.game.get_actor_by_name(name)
        self.game.tribunal.submit_lynch_vote(actor, vote)
        if vote:
            await interaction.send("Voted Yes", ephemeral=True, delete_after=0.0)

    async def lynch_vote_yes(self, interaction: "disnake.Interaction") -> None:
        await self.handle_lynch_vote(interaction, True)

    async def lynch_vote_no(self, interaction: "disnake.Interaction") -> None:
        await self.handle_lynch_vote(interaction, False)

    async def lynch_vote_abstain(self, interaction: "disnake.Interaction") -> None:
        await self.handle_lynch_vote(interaction, None)


class InputController:
    """
    Basically just a collection of InputPanel
    """

    def __init__(self, game: "Game", router: "Router") -> None:
        self._panels: T.Dict["disnake.User", "InputPanel"] = dict()
        self._actor_to_panel: T.Dict["Actor", "InputPanel"] = dict()
        self._game = game
        self._router = router

    @property
    def game(self) -> "Game":
        return self._game

    def add_panel(self, user: "disnake.User", debug: bool = False) -> "InputPanel":
        actor = self._game.get_actor_by_name(user.name)
        if actor is None:
            print(f"WARNING: unknown actor by name {user.name}")
        ip = InputPanel(user, actor, self._router, debug=debug)
        self._panels[user] = ip
        self._actor_to_panel[actor] = ip
        return ip

    def get_panel(self, user: "disnake.User") -> T.Optional["InputPanel"]:
        if user not in self._panels:
            return None
        return self._panels[user]

    def get_panel_by_actor(self, actor: "Actor") -> T.Optional["InputPanel"]:
        if actor not in self._actor_to_panel:
            return None
        return self._actor_to_panel[actor]

    def remove_panel(self, user: "disnake.User") -> None:
        if user in self._panels:
            panel = self._panels.pop(user)
        for key, value in self._actor_to_panel.items():
            if panel == value:
                break
        else:
            return
        self._actor_to_panel.pop(key)

    def drive(self) -> None:
        """
        Drive all input panel updates
        """
        for panel in self._panels.values():
            panel.drive()
