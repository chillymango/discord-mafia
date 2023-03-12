import asyncio
import logging
import time
import typing as T

from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.webhook import don_bot_message
from engine.actor import Actor
from engine.message import Message
from engine.message import MessageType
from engine.resolver import SequenceEvent
import log
from proto import command_pb2
from proto import service_pb2_grpc
from proto import connect_pb2
from proto import message_pb2
from proto import state_pb2

if T.TYPE_CHECKING:
    from grpc import ServicerContext
    from chatapi.app.bot import BotUser
    from chatapi.app.bot_api import BotApi
    from engine.message import Messenger

logger = logging.getLogger(name=__name__)
logger.addHandler(log.ch)


# TODO: replace message object with this
class MessageExport:

    @classmethod
    def create(cls, message: "Message") -> message_pb2.Message:
        if message.message_type == MessageType.ANNOUNCEMENT:
            return cls.create_announcement(message)
        if message.message_type == MessageType.BOT_PUBLIC_MESSAGE:
            return cls.create_bot_public_message(message)
        if message.message_type == MessageType.PLAYER_PUBLIC_MESSAGE:
            return cls.create_player_public_message(message)
        if message.message_type == MessageType.PRIVATE_MESSAGE:
            return cls.create_private_message(message)
        if message.message_type == MessageType.PRIVATE_FEEDBACK:
            return cls.create_private_feedback(message)
        if message.message_type == MessageType.INDICATOR:
            return cls.create_indicator(message)
        if message.message_type == MessageType.NIGHT_SEQUENCE:
            return cls.create_night_sequence(message)
        print(f"Unknown message type {message.message_type.name}")
        raise ValueError(f"Unknown message type {message.message_type.name}")

    @classmethod
    def create_announcement(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.GAME,
            message=message.message,
            title=message.title,
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )

    @classmethod
    def create_bot_public_message(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.PUBLIC,
            message=f"{message.addressed_from.name}:{message.message}",
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )

    @classmethod
    def create_player_public_message(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.PUBLIC,
            message=f"{message.addressed_from.name}:{message.message}",
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )

    @classmethod
    def create_private_message(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.PRIVATE,
            message=f"{message.addressed_from.name}:{message.message}",
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )

    @classmethod
    def create_private_feedback(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.FEEDBACK,
            title=message.title,
            message=message.message,
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )

    @classmethod
    def create_indicator(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.GAME,
            title=message.title,
            message=message.message,
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )

    @classmethod
    def create_night_sequence(cls, message: "Message") -> message_pb2.Message:
        return message_pb2.Message(
            timestamp=message.real_time,
            source=message_pb2.Message.GAME,
            message=f"{message.title}:{message.message}",
            turn_number=message.turn_number,
            turn_phase=message.turn_phase.value,
        )


class GrpcBotApi(service_pb2_grpc.GrpcBotApiServicer):

    _bot_api: T.Optional["BotApi"] = None
    _subscribed: T.Set["BotUser"] = set()

    def set_bot_api(self, api: "BotApi") -> None:
        self._bot_api = api

    def get_bot(self, bot_id: str) -> "BotUser":
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")

        bot = self._bot_api.get_bot_by_id(bot_id)
        if bot is None:
            raise ValueError(f"Cannot find bot with ID {bot_id}")

        return bot

    def Connect(self, request: connect_pb2.ConnectRequest, context):
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
        print(f"Vending {bot.name}")
        response = connect_pb2.ConnectResponse()
        response.timestamp = time.time()
        response.bot_name = bot.name
        response.bot_id = bot.id
        return response

    def Disconnect(self, request: connect_pb2.DisconnectRequest, context):
        """
        Handle a bot service disconnecting from a game bot.
        """
        bot = self.get_bot(request.bot_id)
        self._bot_api.check_in_bot(bot.name)
        logger.debug(f"Disconnected. {self._bot_api.reserved_bots or 'No'} bots being held.\n"
                     f"{[bot.name for bot in self._bot_api.free_bots]} are free.")

        response = connect_pb2.DisconnectResponse()
        response.timestamp = time.time()
        response.success = True
        return response

    def GetGame(self, request: state_pb2.GetGameRequest, ctx):
        bot = self.get_bot(request.bot_id)

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

    async def SubscribeMessages(self, request: message_pb2.SubscribeMessagesRequest, context: "ServicerContext"):
        """
        What does this actually do lol

        I guess we could just make it yield fake messages as a test
        """
        driver = self._bot_api.get_bot_driver_by_id(request.bot_id)
        while True:
            try:
                # we send one message every second as a keep-alive i guess?
                msgs = []
                while driver._grpc_queue.qsize() > 0:
                    game_msg = driver._grpc_queue.get_nowait()
                    msgs.append(MessageExport.create(game_msg))
                response = message_pb2.SubscribeMessagesResponse(timestamp=time.time(), messages=msgs)
                yield response
            except Exception as exc:
                logger.exception(exc)
            finally:
                await asyncio.sleep(1.0)

    def SendMessage(self, request: message_pb2.SendMessageRequest, context) -> message_pb2.SendMessageResponse:
        # this is where the fun begins?
        bot = self.get_bot(request.bot_id)
        self._bot_api.public_message(bot.id, request.message.message)
        return message_pb2.SendMessageResponse(timestamp=time.time(), success=True)

    def submit_target(self, request: command_pb2.TargetRequest, api_call: T.Callable) -> command_pb2.TargetResponse:
        bot = self.get_bot(request.bot_id)
        bot_actor = self._bot_api.game.get_actor_by_name(bot.name)
        voted_actor = self._bot_api.game.get_actor_by_name(request.target_name, raise_if_missing=True)
        api_call(bot_actor, voted_actor)
        try:
            for action in bot_actor.role.day_actions() + bot_actor.role.night_actions():
                if action.instant():
                    SequenceEvent(action(), voted_actor).execute()
        except Exception as exc:
            logger.exception(exc)

        return command_pb2.TargetResponse(timestamp=time.time())

    def TrialVote(self, request: command_pb2.TargetRequest, context) -> command_pb2.TargetResponse:
        return self.submit_target(request, self._bot_api.game.tribunal.submit_trial_vote)

    def LynchVote(self, request: command_pb2.BoolVoteRequest, context) -> command_pb2.BoolVoteResponse:
        bot = self.get_bot(request.bot_id)
        bot_actor = self._bot_api.game.get_actor_by_name(bot.name)
        self._bot_api.game.tribunal.submit_lynch_vote(bot_actor, request.vote)
        return command_pb2.TargetResponse(timestamp=time.time())

    def SkipVote(self, request: command_pb2.BoolVoteRequest, context) -> command_pb2.BoolVoteResponse:
        bot = self.get_bot(request.bot_id)
        bot_actor = self._bot_api.game.get_actor_by_name(bot.name)
        self._bot_api.game.tribunal.submit_skip_vote(bot_actor, request.vote)
        return command_pb2.TargetResponse(timestamp=time.time())

    def DayTarget(self, request: command_pb2.TargetRequest, context) -> command_pb2.BoolVoteResponse:
        return self.submit_target(request, Actor.choose_targets)

    def NightTarget(self, request: command_pb2.TargetRequest, context) -> command_pb2.BoolVoteResponse:
        return self.submit_target(request, Actor.choose_targets)

    def LastWill(self, request: message_pb2.LastWillRequest, context) -> message_pb2.LastWillResponse:
        self._bot_api.submit_last_will(request.bot_id, request.last_will)
        return message_pb2.LastWillResponse(timestamp=time.time(), success=True)


# TODO: split this by game eventually, but
# it must be accessible early by bot
api: GrpcBotApi = GrpcBotApi()
