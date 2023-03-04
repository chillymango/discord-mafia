import asyncio
import time
import typing as T

from proto import connect_pb2
from proto import connect_pb2_grpc

if T.TYPE_CHECKING:
    from chatapi.app.bot_api import BotApi


class ManageSessionImpl(connect_pb2_grpc.ManageSessionServicer):
    """
    Handle connect and disconnect requests
    """

    _bot_api: T.Optional["BotApi"] = None

    def set_bot_api(self, api: "BotApi") -> None:
        self._bot_api = api

    def Connect(self, request: connect_pb2.ConnectRequest, ctx):
        """
        Handle a bot service requesting a game bot.
        """
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")
        
        requested_name = request.request_name
        bot = self._bot_api.check_out_bot(bot_name=requested_name)
        if bot is None and requested_name:
            raise ValueError(f"Could not reserve bot with name {requested_name}")
        if bot is None:
            raise ValueError(f"Could not reserve a bot. We appear to be out.")

        # give the basic information about the bot
        response = connect_pb2.ConnectResponse()
        response.timestamp = time.time()
        response.bot_name = bot.name
        response.bot_id = bot.id
        return response

    def Disconnect(self, request: connect_pb2.DisconnectRequest, ctx):
        """
        Handle a bot service disconnecting from a game bot.
        """
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")

        bot = self._bot_api.get_bot_by_id(request.bot_id)
        if bot is None:
            raise ValueError(f"Cannot find bot with ID {request.bot_id}")
        self._bot_api.check_in_bot(bot.name)
        print(f"Disconnected. {self._bot_api.reserved_bots or 'No'} bots being held.\n"
              f"{[bot.name for bot in self._bot_api.free_bots]} are free.")

        response = connect_pb2.DisconnectResponse()
        response.timestamp = time.time()
        response.success = True
        return response


_cleanup_coroutines = []

async def test() -> None:
    """
    Instantiate the above servicer and run a test.
    Prepare the DonBot to talk to this thing as well.
    """
    from grpc import aio
    from chatapi.app.bot import BotUser
    from chatapi.app.bot_api import BotApi
    from engine.game import Game
    from engine.player import Player
    from engine.setup import do_setup

    BIND = 'localhost:50051'
    g = Game()
    bot_p = [
        Player.create_from_bot(BotUser("Albot")),
        Player.create_from_bot(BotUser("Anthobot-3000")),
        Player.create_from_bot(BotUser("Brandroid")),
        Player.create_from_bot(BotUser("Jerri-tron")),
        Player.create_from_bot(BotUser("Mimicron")),
        Player.create_from_bot(BotUser("Willbot")),
        # fuck
    ]
    bot_p.extend([Player.create_from_bot(BotUser(str(x))) for x in range(15 - len(bot_p))])
    g.add_players(*bot_p)
    success, msg = do_setup(g, override_player_count=True)
    print(success)
    print(msg)

    server_impl = ManageSessionImpl()
    api = BotApi(g)
    server_impl.set_bot_api(api)

    server = aio.server()
    connect_pb2_grpc.add_ManageSessionServicer_to_server(server_impl, server)
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
