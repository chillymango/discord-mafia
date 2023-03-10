import asyncio
import typing as T

import disnake

from chatapi.discord.chat import CHAT_DRIVERS

if T.TYPE_CHECKING:
    from chatapi.discord.town_hall import TownHall
    from engine.game import Game


class Court:
    """
    Implements the Court mechanic for Judge

    This object should mostly deal with managing the chat
    """

    def __init__(self, game: "Game", channel: "disnake.TextChannel") -> None:
        # this should live inside townhall so not sure if this ref is needed
        self._game = game
        self._channel = channel
        self._stop = asyncio.Event()

        # i guess we only set this up if we have a Judge in the game?
        # NOTE: for simplicity, messenger shouldn't be aware of this chat driver
        if channel in CHAT_DRIVERS:
            self._chat_driver = CHAT_DRIVERS[channel]
        else:
            # TODO: fix circ import?
            from chatapi.discord.driver import ChatDriver
            self._chat_driver = ChatDriver(game, channel)
            CHAT_DRIVERS[channel] = self._chat_driver

        self._anonymous_automod_rule: "disnake.AutoModRule" = None

    def stop(self) -> None:
        self._stop.set()

    async def initialize(self) -> None:
        """
        Should be called inside event loop.
        """
        await self._chat_driver.setup_webhook("CourtChat")
        self._chat_driver.start()

        # if we cannot find the automod rule here, complain loudly
        all_rules = await self._channel.guild.fetch_automod_rules()
        for rule in all_rules:
            if rule.name == "Anonymity":
                break
        else:
            raise ValueError("Could not find the Court anonymity AutoMod rule")

        self._anonymous_automod_rule = rule
        await self._anonymous_automod_rule.edit(enabled=False)

    async def run(self, discussion_thread: "disnake.Thread") -> None:
        self._stop.clear()
        try:
            await self.call_court(discussion_thread)
            await self._stop.wait()
        except Exception as exc:
            print(f"Error in calling court")
            print(repr(exc))

        await self.resolve_court()

    async def call_court(self, discussion_thread: "disnake.Thread") -> None:
        """
        This is the primary action trigger.

        This is probably done from Town Hall.
        Town Hall should provide a discussion thread to convert into Court.
        """
        # enable the automod rule
        await self._anonymous_automod_rule.edit(enabled=True)
        await discussion_thread.edit(name="Court is In Session")
        embed = disnake.Embed(
            title="The Judge Has Called Court",
            description="Court is now in session.\n"
                "Use the **/chat** command to speak.\n"
                "The following rules apply during Court:\n"
                " - All ballots are anonymous.\n"
                " - The Judge gets extra votes and can speak as the Court.\n"
                " - The Crier can speak as the Court.\n"
                " - There is no Trial Defense. A vote will immediately proceed to lynch.\n"
        )
        await self._channel.send(embed=embed)
        self._chat_driver.set_discussion_thread(discussion_thread)

    async def resolve_court(self) -> None:
        """
        This should get called after the day ends to resolve court.
        """
        print("Resolving Court")
        # disable the automod rule
        await self._anonymous_automod_rule.edit(enabled=False)
        # town hall will clean up the thread
        self._chat_driver.set_discussion_thread(None)
