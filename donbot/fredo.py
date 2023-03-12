"""
He's a bit dim witted but he had the right spirit

May he rest in peace
"""
import asyncio
import typing as T

from academy import ChatContext
from academy import ChatGPTBot
from academy import Prompt
from donbot import DonBot
from donbot.action import BotAction
from engine.phase import TurnPhase


class FredoBot(DonBot):
    """
    \"Intelligent\" player

    Replace the default random resolver with an AI resolver
    """

    def __init__(self, bot_name: str = None, debug: bool = False) -> None:
        super().__init__(bot_name=bot_name, debug=debug)

    def setup_resolvers(self) -> None:
        self._ai_resolver = ChatGPTBot(self.name, self.role.name, debug=self._debug)
        self._resolvers = {ba: self._ai_resolver.get_action_handler(ba) for ba in BotAction}

    async def print_message_task(self) -> None:
        """
        Feed the message to the resolver so it can update its chat contex
        """
        while True:
            try:
                msg = await self._message_queue.get()
                # feed resolver with this information
                # if it's an action feedback, update last will
                self._ai_resolver.ingest_proto(msg)
                # TODO: could use the game event log to update chat context?
                await self._maybe_record_feedback(msg)
            except asyncio.CancelledError:
                break

    async def subscribe_messages(self) -> None:
        await super().subscribe_messages()
        self._speech_task = asyncio.create_task(self.speech_task())

    async def speech_task(self) -> None:
        """
        This is what makes you special buddy, you'll actually talk to the Town!

        Speech Task involves the following asynchronous actions:
            * examine received public and private chat messages
            * condense them into a message format for an interaction
            * ask for a response to the chat using latest context
        """
        while True:
            # pause if we can't say anything
            try:
                if TurnPhase[self._game.turn_phase] not in (TurnPhase.DAYLIGHT,):
                    continue
                # prompt for speech with the current conversation as context
                to_say = await self._ai_resolver.iter_conversation()
                # split it into response_context: answer
                #response_context, _, answer = to_say.partition(':')
                if 'NA' in to_say:
                    continue
                self.log.info(f"I will say: [{to_say}]")
                self._outbound_queue.put_nowait(to_say)
                #to_say = 'this is just a test'
                #self.log.info(f"Response Context: {response_context}")
                #self.log.info(f"I will say: [{answer}]")
                #self._outbound_queue.put_nowait(answer)

                # if there's a lull in the conversation, or there are too many
                # messages in the current conversation, roll over to a new one
                # TODO: (implement above)
                # lets just see if we can get talking working now
                # if conversation length exceeds some critical length, roll-over conversation
                # as a digestible
                await self._ai_resolver.maybe_roll_over_conversation()

            except KeyboardInterrupt as interrupt:
                raise
            except Exception as exc:
                self.log.exception(exc)
            finally:
                # don't bankrupt me now
                # TODO: why the fuck didn't this work
                await asyncio.sleep(15.0)


async def fredo(debug: bool = True) -> None:
    bot = FredoBot(debug=debug)
    await bot.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    asyncio.run(fredo(debug=not args.live))
