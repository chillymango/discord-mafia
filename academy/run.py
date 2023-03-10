import asyncio
import threading

from academy import ChatGPTBot

from chatapi.discord.driver import BotMessageDriver

from engine.actor import Actor
from engine.game import Game
from engine.message import Message
from engine.message import MessageType
from engine.message import Messenger
from engine.phase import TurnPhase
from engine.player import Player
from engine.setup import do_setup
from engine.stepper import sleep_override
from engine.stepper import Stepper


def inject_public(actor: "Actor", msg: str) -> None:
    """
    Debugging tool
    """
    messenger = actor.game.messenger
    if not messenger:
        print(f"No messenger. Dropping message: {msg}")
        return
    messenger.queue_message(Message.player_public_message(actor, msg))


async def do_day(actor: "Actor", bot: "ChatGPTBot") -> None:
    if actor.has_day_action:
        # ask if we want to use day action, and if so, to target who
        decision = bot.make_decision(
            f"You may choose to use your ability. {actor.role.day_action_description()}.",
            choices=["Nobody"] + actor.get_target_options(as_str=True)
        )

        target = actor.game.get_actor_by_name(decision)
        if target is None:
            print("Since no target could be identified, skipping targeting")
        else:
            actor.choose_targets(target)

    # trial vote meter?
    # suspicion meter?
    suspicion = bot.make_decision(
        f"Choose someone that you are suspicious of. Avoid choosing without " \
        f"evidence. You can Nobody if you are not suspicious of anybody.",
        choices=['Nobody'] + [actor.name for actor in actor.game.get_live_actors()]
    )
    if suspicion != 'Nobody':
        target = actor.game.get_actor_by_name(suspicion)

    if target is not None:
        actor.game.tribunal.submit_trial_vote(actor, target)
        bot.make_speech(f"You have voted to put {target.name} on trial")
        # TODO: lynch logic


async def main() -> None:
    game = Game()
    player_names = [
        "Zhuge Liang",
        "Liu Bei",
        "Zhang Fei",
        "Guan Yu",
        "Zhao Yun",
        "Cao Cao",
        "Sima Yi",
        "Yuan Shao",
        "Yuan Shu",
        "Kong Zhou",
        "Liu Biao",
        "Sun Quan",
        "Zhou Yu",
        "Lu Bu",
        "Dong Zhuo",
    ]
    game.add_players(*[Player(pname) for pname in player_names])
    result, msg = do_setup(game, skip=True)
    game.debug_override_role("Zhuge Liang", "Investigator")
    game.debug_override_role("Cao Cao", "Mayor")
    if not result:
        raise ValueError(f"Failed to setup game: {msg}")
    #bot = ChatGPTBot(name="Zhuge Liang", role_name="Investigator")
    bots = [ChatGPTBot(name=actor.name, role_name=actor.role.name, debug=True)
            for actor in game.get_actors()]
    bot_drivers = [BotMessageDriver(actor) for actor in game.get_actors()]
    messenger = Messenger(game, *bot_drivers)
    game.messenger = messenger
    messenger.start()

    async def printout(bot: ChatGPTBot, driver: BotMessageDriver) -> None:
        while True:
            msg = await driver.grpc_queue.get()
            print(f"Message: {msg}")
            # give this to the bot
            bot.ingest(msg)

    tasks = []
    for bot, driver in zip(bots, bot_drivers):
        tasks.append(asyncio.create_task(printout(bot, driver)))

    while True:
        print(f"{game._turn_phase.name} {game.turn_number}")
        if game.turn_phase == TurnPhase.DAYLIGHT:


        elif game.turn_phase == TurnPhase.NIGHT:
            # pick a night target
            if actor.has_night_action:
                # TODO: what about multiple decisions?
                decision = bot.make_decision(
                    f"You may choose to use your ability. {actor.role.night_action_description()}.",
                    choices=["Nobody"] + actor.get_target_options(as_str=True)
                )

                try:
                    target = game.get_actor_by_name(decision)
                except:
                    target = None

                if target is None:
                    print("Since no target could be identified, skipping targeting")
                else:
                    actor.choose_targets(target)

        await skipper.step()
        await asyncio.sleep(0.1)  # NOTE: we need to yield here to let other things run
        import pdb; pdb.set_trace()



def old():
    bot = ChatGPTBot(name="Zhuge Liang", role_name="Investigator", debug=False)

    # create a bot message driver for our bot user
    # fuckin yolo what could possibly go wrong
    actor = game.get_actor_by_name("Zhuge Liang")
    cao_cao = game.get_actor_by_name("Cao Cao")
    driver = BotMessageDriver(actor)
    messenger = Messenger(game, driver)
    game.messenger = messenger
    messenger.start()

    # create a consumer
    async def printout() -> None:
        while True:
            msg = await driver.grpc_queue.get()
            print(f"Message: {msg}")
            # give this to the bot
            bot.ingest(msg)

    asyncio.create_task(printout())

    skipper = Stepper(game, {}, sleeper=sleep_override)

    while True:
        print(f"{game._turn_phase.name} {game.turn_number}")
        if game.turn_phase == TurnPhase.DAYLIGHT:
            if actor.has_day_action:
                # ask if we want to use day action, and if so, to target who
                decision = bot.make_decision(
                    f"You may choose to use your ability. {actor.role.day_action_description()}.",
                    choices=["Nobody"] + actor.get_target_options(as_str=True)
                )

                target = game.get_actor_by_name(decision)
                if target is None:
                    print("Since no target could be identified, skipping targeting")
                else:
                    actor.choose_targets(target)

            # trial vote meter?
            # suspicion meter?
            suspicion = bot.make_decision(
                f"Choose someone that you are suspicious of. Avoid choosing without " \
                f"evidence. You can Nobody if you are not suspicious of anybody.",
                choices=['Nobody'] + [actor.name for actor in game.get_live_actors()]
            )
            if suspicion != 'Nobody':
                target = game.get_actor_by_name(suspicion)

            if target is not None:
                game.tribunal.submit_trial_vote(actor, target)
                bot.make_speech(f"You have voted to put {target.name} on trial")
                # TODO: lynch logic

        elif game.turn_phase == TurnPhase.NIGHT:
            # pick a night target
            if actor.has_night_action:
                # TODO: what about multiple decisions?
                decision = bot.make_decision(
                    f"You may choose to use your ability. {actor.role.night_action_description()}.",
                    choices=["Nobody"] + actor.get_target_options(as_str=True)
                )

                try:
                    target = game.get_actor_by_name(decision)
                except:
                    target = None

                if target is None:
                    print("Since no target could be identified, skipping targeting")
                else:
                    actor.choose_targets(target)

        await skipper.step()
        await asyncio.sleep(0.1)  # NOTE: we need to yield here to let other things run
        import pdb; pdb.set_trace()

    # post-init to daybreak
    await skipper.step()
    # daybreak to daylight
    await skipper.step()
    # daylight to dusk
    await skipper.step()
    # dusk to night
    await skipper.step()

    # Ok so now it's night, we should be able to target and test
    #actor.choose_targets(cao_cao)
    # ask for an output and choose
    test = bot.make_decision("You must choose someone to investigate", [actor.name for actor in game.get_actors()])
    await asyncio.sleep(1.0)

    await skipper.step()

    # it should be daybreak here
    await skipper.step()
    # it should be daylight here

    await asyncio.sleep(1.0)
    import pdb; pdb.set_trace()


if __name__ == "__main__":
    asyncio.run(main())
