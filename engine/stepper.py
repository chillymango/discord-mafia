"""
Advance game states

The stepper should know how to take in a game, look at its current state,
and advance game logic.
"""
import asyncio
import random
import time
import typing as T
from collections import defaultdict

from engine.message import Message
from engine.phase import GamePhase
from engine.phase import TurnPhase
from engine.resolver import SequenceEvent

if T.TYPE_CHECKING:
    from engine.game import Game
    from engine.message import Messenger


Sleeper = T.Callable[[float], T.Union[None, T.Coroutine]]


async def sleep_override(duration: float) -> T.Coroutine:
    pass


class Stepper:
    """
    Takes a config and updates game states.

    We rely on config primarily for timings.
    """

    def __init__(self, game: "Game", config: T.Dict[str, T.Any], sleeper: Sleeper = asyncio.sleep) -> None:
        self._sleep = sleeper
        self._game = game
        self._config = config
        self._init_with_config()

    @property
    def messenger(self) -> "Messenger":
        return self._game.messenger

    def _init_with_config(self) -> None:
        self._daybreak_to_daylight = self._config.get("daybreak_to_daylight_override", 5.0)
        self._day_duration = self._config.get("day_duration", 60.0)
        self._dusk_to_night = self._config.get("dusk_to_night_override", 5.0)
        self._night_duration = self._config.get("night_duration", 30.0)
        self._night_sequence_duration = self._config.get("night_sequence_override", 1.0)

    async def _flush_then_wait_for_min_time(self, delay: float, min_time: float) -> None:
        """
        Flush all messages and then wait for some minimum duration
        """
        t_init = time.time()
        #self._game.flush_all_messages()
        t_final = time.time()
        t_remaining = min_time - (t_final - t_init)
        await self._sleep(max(t_remaining, 0))

    async def _post_initialization(self) -> None:
        """
        Phase: Post-Init

        Handle post-init into Daylight
        """
        print("Transitioning Post-Init to Daybreak")
        # phase advancing should be done last
        self._game.turn_phase = TurnPhase.DAYBREAK

    async def _to_daylight(self) -> None:
        """
        Phase: Daybreak

        Handle daybreak to daylight transition
        """
        intro = random.choice([
            "A new dawn breaks as the sun rises, marking the start of a brand new day "
            "filled with endless possibilities.",
            "The golden orb ascends into the sky, bringing forth a fresh beginning and "
            "a clean slate for all.",
            "As the first rays of sunlight peek over the horizon, the world awakens to "
            "a fresh start and a chance to create new memories.",
            "A new chapter begins as the sun rises, signaling a new opportunity to "
            "embrace life with renewed energy and enthusiasm.",
            "With the rising of the sun comes a fresh start and a chance to make "
            "the most of every moment.",
            "The sun's ascent into the sky marks the beginning of a new day, a blank "
            "canvas waiting to be painted with new experiences and adventures.",
            "As the sun rises, so does the potential for growth, renewal, and positivity "
            "in all aspects of life.",
            "The morning sun's arrival brings with it a sense of hope and optimism, "
            "inspiring a sense of purpose and motivation to tackle the day's challenges.",
            "With each new dawn comes the promise of a fresh start and a chance to chase "
            "one's dreams with renewed vigor and determination.",
            "As the sun ascends into the sky, it illuminates the path ahead, encouraging "
            "us to step boldly into the future and seize the day.",
        ])
        self.messenger.queue_message(Message.announce(
            self._game,
            title=f"Day {self._game.turn_number}",
            message=intro
        ))
        print("Transitioning to Daylight")
        self._game.kill_report.transition()
    
        # TODO: coded transition durations
        await self._flush_then_wait_for_min_time(3.0, self._daybreak_to_daylight)
    
        # phase advancing should be done last
        self._game.turn_phase = TurnPhase.DAYLIGHT

    async def _to_dusk(self) -> None:
        """
        Phase: Daylight

        Handle daylight to dusk transition
        """
        print("Transitioning to Dusk")
        # Tribunal object should be driving most of the interaction during Daylight
        await self._game.tribunal.do_daylight()
        await self._flush_then_wait_for_min_time(2.0, 0.0)

        # phase advancing should be done last
        self._game.turn_phase = TurnPhase.DUSK

    async def _to_night(self) -> None:
        """
        Phase: Dusk

        Handle dusk to night transition
        """
        # put somebody in jail lol
        print("Transitioning to Night")

        await self._flush_then_wait_for_min_time(2.0, self._dusk_to_night)
    
        # phase advancing should be done last
        self._game.turn_phase = TurnPhase.NIGHT

    async def _to_night_sequence(self) -> None:
        """
        Phase: Night

        Handle night to night sequence transition
        """
        outro = random.choice([
            "As the sun sinks beneath the horizon, the moon ascends into the sky, "
            "casting a soft, ethereal glow across the world.",
            "With the setting of the sun comes the rise of the moon, signaling the "
            "end of one day and the start of another.",
            "As the last rays of sunlight disappear, the moon takes its place in the "
            "sky, illuminating the darkness with its gentle radiance.",
            "The sun's descent marks the transition from day to night, with the moon "
            "rising to take its place as the guiding light.",
            "As the sun sets, the moon rises, casting a serene and tranquil ambiance "
            "over the world below.",
            "With the sunset comes a sense of calm and tranquility, as the moon rises "
            "to provide a comforting source of light in the darkness.",
            "As the sun disappears beyond the horizon, the moon rises to offer a sense "
            "of serenity and peace to all who gaze upon it.",
            "With the setting of the sun and the rise of the moon, the world transitions "
            "from the hustle and bustle of the day to the stillness and quiet of the night.",
            "The setting sun and the rising moon create a stunning contrast, signaling the "
            "end of one cycle and the start of another.",
            "As the sun bids farewell to the day, the moon rises to cast its enchanting "
            "spell over the world, a gentle reminder of the beauty that exists in the darkness.",
        ])
        self.messenger.queue_message(Message.announce(
            self._game,
            title=f"Night {self._game.turn_number}",
            message=outro
        ))
        print("Night to Night Sequence")    
        # TODO: coded transition durations
        # the primary messages that may accumulate here are appropriate to collect at the end
        # of the NIGHT phase
        await self._flush_then_wait_for_min_time(2.0, self._night_duration)
    
        # phase advancing should be done last
        self._game.turn_phase = TurnPhase.NIGHT_SEQUENCE

    async def _to_daybreak(self) -> None:
        """
        Phase: Night Sequence

        Process the night sequence and transition to daybreak
        """
        print("Transitioning to Daybreak")
    
        # take all live actors and their targets and create SequenceEvent objects for them
        events: T.List[SequenceEvent] = []
        for actor in self._game.get_live_actors():
    
            actor.reset_health()
    
            for action_class in actor.role.night_actions():
                # TODO: kinda inefficient but whatevs hack it
                action = action_class()
                events.append(SequenceEvent(action, actor))
    
        # process events in order -- group them by ORDER attribute value
        grouped_events: T.Dict[int, T.List[SequenceEvent]] = defaultdict(list)
        for event in events:
            grouped_events[event.action.ORDER].append(event)
    
        for order_key in sorted(grouped_events.keys()):
            print(f"Doing events for {order_key}")
            # prune at each distinct order key value
            # this is done in order to make sure that kills process before investigative actions
            # and that downstream actions are never processed by dead people
            # upstream actions like bus driving and roleblocking will still apply though
            #
            # all kill actions should process simultaneously
            # e.g if vigilante and mafioso both target each other, they should both die, instead
            # of leaving one of them to get resolved first, and one of them alive as a result
            valid_events = [ev for ev in grouped_events[order_key] if ev.actor.is_alive]
            for ev in valid_events:
                ev.execute()

        await self._flush_then_wait_for_min_time(2.0, self._night_sequence_duration)
    
        for actor in self._game.get_live_actors():
            # TODO: something that manages this for us would be nice?
            actor.consume_vest()
    
        # phase advancing should be done last
        self._game.turn_phase = TurnPhase.DAYBREAK
        self._game.turn_number += 1

    def advance(self, sleep: Sleeper=sleep_override, loop: asyncio.AbstractEventLoop = None) -> None:
        """
        For debugging and initialization purposes, immediately step
        the game forward.
    
        This runs all required coroutines synchronously.
        The sleep function is by default overridden to a bypass, but can be set to anything.
        """
        loop = loop or asyncio.get_event_loop() or asyncio.new_event_loop()
        if self._game.turn_phase == TurnPhase.INITIALIZING:
            loop.run_until_complete(self._post_initialization())
            return
        if self._game.turn_phase == TurnPhase.DAYBREAK:
            loop.run_until_complete(self._to_daylight())
            return
        if self._game.turn_phase == TurnPhase.DAYLIGHT:
            loop.run_until_complete(self._to_dusk())
            return
        if self._game.turn_phase == TurnPhase.DUSK:
            loop.run_until_complete(self._to_night())
            return
        if self._game.turn_phase == TurnPhase.NIGHT:
            loop.run_until_complete(self._to_night_sequence())
            return
        if self._game.turn_phase == TurnPhase.NIGHT_SEQUENCE:
            loop.run_until_complete(self._to_daybreak())
            return
        
        raise ValueError(f"Unknown turn phase {self._game.turn_phase}")

    async def step(self) -> None:
        """
        Asynchronously step the game forward.
        This typically involves some sort of timed waiting.
        """
        if self._game.turn_phase == TurnPhase.INITIALIZING:
            return await self._post_initialization()
        if self._game.turn_phase == TurnPhase.DAYBREAK:
            return await self._to_daylight()
        if self._game.turn_phase == TurnPhase.DAYLIGHT:
            return await self._to_dusk()
        if self._game.turn_phase == TurnPhase.DUSK:
            return await self._to_night()
        if self._game.turn_phase == TurnPhase.NIGHT:
            return await self._to_night_sequence()
        if self._game.turn_phase == TurnPhase.NIGHT_SEQUENCE:
            return await self._to_daybreak()
    
        raise ValueError(f"Unknown turn phase {self._game.turn_phase}")
