"""
Run the app in production mode?
"""
import asyncio
import platform
if platform.system()=='Windows':
    # what the fuck?
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import typing as T
from grpc import aio

from chatapi.app.grpc.api import GrpcBotApi
from chatapi.app.bot_api import BotApi

from proto import service_pb2_grpc

if T.TYPE_CHECKING:
    from engine.game import Game

BIND = 'localhost:50051'

_cleanup_coroutines = []

async def run_grpc_server(game: "Game", bind=BIND):
    api = GrpcBotApi()
    bot_api = BotApi(game)
    api.set_bot_api(bot_api)

    server = aio.server()
    service_pb2_grpc.add_GrpcBotApiServicer_to_server(api, server)
    server.add_insecure_port(bind)
    try:
        print("gRPC server start")
        await server.start()
    finally:
        async def server_graceful_shutdown():
            # Shuts down the server with 0 seconds of grace period. During the
            # grace period, the server won't accept new connections and allow
            # existing RPCs to continue within the grace period.
            await server.stop(5)

        global _cleanup_coroutines
        _cleanup_coroutines.append(server_graceful_shutdown())
        await server.wait_for_termination()
