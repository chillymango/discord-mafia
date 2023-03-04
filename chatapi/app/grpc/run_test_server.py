import asyncio
from grpc import aio
from chatapi.app.bot import BotUser
from chatapi.app.bot_api import BotApi
from chatapi.app.grpc.api import GrpcBotApi
from chatapi.app.grpc.connect import ManageSessionImpl
from chatapi.app.grpc.state import StateImpl
from engine.game import Game
from engine.player import Player
from engine.setup import do_setup

from proto import service_pb2_grpc

from proto import connect_pb2_grpc
from proto import state_pb2_grpc


_cleanup_coroutines = []

async def test() -> None:
    BIND = 'localhost:50051'
    g = Game()
    bot_p = [
        Player.create_from_bot(BotUser("George Washington")),
        Player.create_from_bot(BotUser("Thomas Jefferson")),
        Player.create_from_bot(BotUser("Andrew Jackson")),
        Player.create_from_bot(BotUser("Abraham Lincoln")),
        Player.create_from_bot(BotUser("Theodore Roosevelt")),
        Player.create_from_bot(BotUser("Woodrow Wilson")),
        Player.create_from_bot(BotUser("Franklin D. Roosevelt")),
        Player.create_from_bot(BotUser("John F. Kennedy")),
        Player.create_from_bot(BotUser("Richard Nixon")),
        Player.create_from_bot(BotUser("George H.W Bush")),
        Player.create_from_bot(BotUser("Bill Clinton")),
        Player.create_from_bot(BotUser("George W. Bush")),
        Player.create_from_bot(BotUser("Barack Obama (means family)")),
        Player.create_from_bot(BotUser("Donald Trump")),
        Player.create_from_bot(BotUser("Joe Biden")),
    ]
    bot_p.extend([Player.create_from_bot(BotUser(str(x))) for x in range(15 - len(bot_p))])
    g.add_players(*bot_p)
    success, msg = do_setup(g, override_player_count=True)
    print(success)
    print(msg)

    bot_api = BotApi(g)
    grpc_api = GrpcBotApi()
    grpc_api.set_bot_api(bot_api)

    server = aio.server()
    service_pb2_grpc.add_GrpcBotApiServicer_to_server(grpc_api, server)
    server.add_insecure_port(BIND)
    print("gRPC server start")
    await server.start()

    async def server_graceful_shutdown():
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    global _cleanup_coroutines
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(test())
    except:
        print("Shutting down.")
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
