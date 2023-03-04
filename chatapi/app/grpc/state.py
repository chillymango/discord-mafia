import asyncio
import time
import typing as T

from proto import state_pb2
from proto import state_pb2_grpc

if T.TYPE_CHECKING:
    from chatapi.app.bot_api import BotApi


class StateImpl(state_pb2_grpc.StateServicer):
    """
    Let us fetch game state info.

    Almost always it'll just be fetch the Game proto.

    All I do is move protos ^_^
    """

    _bot_api: T.Optional["BotApi"] = None

    def set_bot_api(self, api: "BotApi") -> None:
        self._bot_api = api

    def GetGame(self, request: state_pb2.GetGameRequest, ctx):
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")

        bot = self._bot_api.get_bot_by_id(request.bot_id)
        if bot is None:
            raise ValueError(f"No bot found with ID {request.bot_id}")

        return state_pb2.GetGameResponse(
            game=self._bot_api.game.to_proto(),
            timestamp=time.time()
        )

    def GetActor(self, request: state_pb2.GetActorRequest, ctx):
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")

        actor = None
        if request.bot_id:
            bot = self._bot_api.get_bot_by_id(request.bot_id)
            actor = self._bot_api.game.get_actor_by_name(bot.name)
        elif request.player_name:
            actor = self._bot_api.game.get_actor_by_name(request.player_name)

        if actor is None:
            raise ValueError(f"Could not find bot with provided identifier")

        return state_pb2.GetActorResponse(
            actor=actor.to_proto(),
            timestamp=time.time(),
        )
