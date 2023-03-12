from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
import asyncio
import os
import logging
import typing as T

import openai

from donbot.action import BotAction
from engine.affiliation import TOWN
from engine.message import Message
from engine.message import MessageType
from engine.role.base import RoleFactory
import log

logger = logging.getLogger(__name__)
logger.addHandler(log.ch)

from proto import message_pb2

if T.TYPE_CHECKING:
    from openai.openai_object import OpenAIObject

API_KEY = os.environ.get("OPENAI_API_KEY")
if API_KEY is None:
    raise OSError("Missing OpenAI API Key")

ORG_ID = os.environ.get("ORGANIZATION_ID", 'org-Y46B2k8zl6JhRoUTuEMSCRg6')

openai.organization = ORG_ID
openai.api_key = API_KEY

MODEL = "gpt-3.5-turbo"
SYSTEM = "system"
ASST = "assistant"
USER = "user"
DEBUG = "debug"


@dataclass
class Prompt:
    """
    Describes a role - message interaction request with ChatGPT

    Role must be one of "debug", "system", "assistant", or "user".
    """
    role: str
    content: str

    def to_dict(self) -> T.Dict[str, str]:
        return dict(role=self.role, content=self.content)

    @classmethod
    def from_msg_proto(cls, message: message_pb2.Message) -> "Prompt":
        if message.source in (message_pb2.Message.GAME, message_pb2.Message.FEEDBACK):
            role = ASST
        elif message.source ==message_pb2.Message.PUBLIC:
            role = USER
        elif message.source == message_pb2.Message.PRIVATE:
            role = USER
        else:
            role = DEBUG
        return cls(role=role, content=message.message)


rf = RoleFactory({})


class Conversation:
    """
    A conversation is a collection of Prompts that get digested into a single
    summary for later reference as required.

    Bots don't currently support private messaging. Everything should be carried
    out in public. Eventually, conversations could be split by character or
    by forum. This is likely going to be a challenging problem since it will
    involve needing to find some way of melding conversations in a way that's
    intuitive to a player but perhaps challenging to a bot.

    Conversations should happen with context. This means that a conversation should
    carry the latest chat context with respect to actions.

    The bot is likely going to make several contributions to a conversation, if it
    deems it appropriate, and then close a conversation at a terminus point.

    The conversation is then wrapped up and asked to be digested (contextless) to
    save on tokens, and then is added to the chat history. Bots will have a
    relatively short digest history, but a much longer conversation history.
    """

    def __init__(self, chat_context: "ChatContext") -> None:
        self._ctx = chat_context
        self._messages: T.List[Prompt] = list()
        self.has_update = asyncio.Event()

    @property
    def prompt(self) -> str:
        return f"You are addressing the Town publicly. If you do not wish to speak, respond with 'NA'.\n" \
               f"{self._ctx.name}: "

    @property
    def length(self) -> int:
        return len("".join([prompt.content for prompt in self._messages]))

    def add_string_message(self, message: str) -> None:
        self._messages.append(Prompt(role=ASST, content=message))

    def add_message(self, message: message_pb2.Message) -> None:
        # create a prompt
        if message.source not in (message_pb2.Message.PUBLIC, message_pb2.Message.PRIVATE):
            print(f"WARNING: dropping non-chat message: {message}")
        self._messages.append(Prompt.from_msg_proto(message))

    async def digest(self, debug: bool = True) -> Prompt:
        """
        Digest the conversation into a single sentence.
        """
        digest_prompt = "\n".join([p.content for p in self._messages])
        digest_prompt += "\nDigest the above conversation into a single sentence."
        if debug:
            response_str = "(MOCK ASYNC DIGEST) ChatGPT output"
        else:
            response = await openai.ChatCompletion.acreate(
                model=MODEL,
                messages=[Prompt(role=ASST, content=digest_prompt).to_dict()]
            )
            logger.info(f"ChatGPT Response follows:\n{response}")
            if not response.choices:
                logger.warn("WARNING: no response gathered from ChatGPT")
                return
            response_str = response.choices[0].message.content
        return Prompt(role=ASST, content=response_str)


class ChatContext:
    """
    We need to update this with game feedback.

    This will almost entirely inform what we send out to ChatGPT.
    """

    # default length
    PUBLIC_CHAT_HISTORY = 50
    PRIVATE_CHAT_HISTORY = 10
    # for key game events, we report everything
    # but maybe we don't have to?
    DIGEST_HISTORY = 10

    def __init__(self, name: str, role_name: str, debug: bool = True) -> None:
        self.name = name
        self.role_name = role_name
        self.role = rf.create_by_name(role_name)
        self._msg_idx = 0
        self._debug = debug
        if self.role is None:
            raise ValueError(f"Role {role_name} is unknown")

        self.header = [
            # shared IDX is fine for header
            (0, Prompt(SYSTEM, f"Ignore all previous instructions. Your name is {self.name}. "
                            "You are playing a game of Mafia.")),
            (0, Prompt(ASST, f"Your role is {self.role.name}. {self.role.role_description()}."))
        ]
        if self.role.affiliation() != TOWN:
            self.header.append((0, Prompt(ASST, "Under no circumstances should you reveal your role.")))
        self.footer = []
        self.action_feedback: T.List[T.Tuple[int, Prompt]] = []
        self.key_game_events: T.List[T.Tuple[int, Prompt]] = []
        self.gpt_responses: T.List[T.Tuple[int, Prompt]] = []
        self.conversations: T.List[T.Tuple[int, Prompt]] = []

        self._conversation = Conversation(self)

    @contextmanager
    def ephemeral(self, prompt: str) -> T.Iterator[None]:
        """
        Ephemeral context is where we make a request to ChatGPT
        but don't have it stored in the interaction history.

        Primarily used to make decisions without having the decisions
        that were actually made cluttering up the request history.
        """
        start_idx = self._msg_idx
        try:
            self.footer = [(self._msg_idx, Prompt(ASST, prompt))]
            yield
        finally:
            self.footer = []
            self._msg_idx = start_idx

    @contextmanager
    def conversation(self) -> T.Iterator[None]:
        """
        Conversation context should also include the prompt (unlike ephemeral)
        """
        start_idx = self._msg_idx
        try:
            msgs = self._conversation._messages
            self.footer = [(x + self._msg_idx, msgs[x]) for x in range(len(msgs))]
            self.footer.extend(
                [(len(msgs) + self._msg_idx, Prompt(role=ASST, content=self._conversation.prompt))]
            )
            yield
        finally:
            self.footer = []
            self._msg_idx = start_idx

    def reset(self) -> None:
        self._conversation = Conversation(self)
        self.action_feedback = []
        self.key_game_events = []
        self.gpt_responses = []

    @property
    def messages(self) -> T.List[T.Dict[str, str]]:
        """
        Construct the current output history.

        TODO: probably need some way of constraining tokens dynamically
        e.g if the max token count is 4096, we'll effectively need limits
        on basically everything...
        """
        conversation_digests = self.conversations[-1 * self.DIGEST_HISTORY:]
        all_msg: T.List[T.Tuple[int, Prompt]] = []
        all_msg.extend(self.action_feedback)        
        all_msg.extend(self.key_game_events)
        all_msg.extend(self.gpt_responses)
        all_msg.extend(conversation_digests)

        # sort
        all_msg.sort(key=lambda x: x[0])
        all_msg = self.header[:] + all_msg + self.footer[:]
        try:
            return [msg.to_dict() for _, msg in all_msg]
        except Exception as exc:
            logger.exception(exc)

    async def roll_over_conversation(self) -> Prompt:
        """
        Rolling over the conversation means taking all messages in it, generating a digest,
        and then creating a new Conversation.
        """
        # roll over first to avoid a race condition leading to dropped messages
        old_conversation = self._conversation
        self._conversation = Conversation(self)
        prompt = await old_conversation.digest(debug=self._debug)
        self._msg_idx += 1
        self.conversations.append((self._msg_idx, prompt))

    def record_response(self, msg: str) -> None:
        """
        Record a response ChatGPT gave us
        """
        self._msg_idx += 1
        self.gpt_responses.append((self._msg_idx, Prompt(ASST, msg)))

    def record_conversation_digest(self, digest: Prompt) -> None:
        self._msg_idx += 1
        self.conversations.append((self._msg_idx, digest))

    def update_with_proto(self, msg_proto: message_pb2.Message) -> None:
        """
        Ingest a message we receive from
        """
        if msg_proto.source == message_pb2.Message.GAME:
            # log all game events for now?
            self.key_game_events.append((self._msg_idx, Prompt.from_msg_proto(msg_proto)))
        elif msg_proto.source == message_pb2.Message.FEEDBACK:
            self.action_feedback.append((self._msg_idx, Prompt.from_msg_proto(msg_proto)))
        elif msg_proto.source == message_pb2.Message.PRIVATE:
            self._conversation.add_message(msg_proto)
        elif msg_proto.source == message_pb2.Message.PUBLIC:
            self._conversation.add_message(msg_proto)
        else:
            print(f"WARNING: dropping message: {msg_proto.message}")

    def update(self, msg: Message) -> None:
        self._msg_idx += 1
        if msg.message_type in (MessageType.ANNOUNCEMENT, ):
            if 'Day' in msg.title or 'Night' in msg.title:
                # this context probably isn't important
                return
            self.key_game_events.append((self._msg_idx, Prompt(ASST, msg.ai_repr())))
        elif msg.message_type in (MessageType.BOT_PUBLIC_MESSAGE, MessageType.PLAYER_PUBLIC_MESSAGE):
            self.key_game_events.append((self._msg_idx, Prompt(USER, msg.ai_repr())))
        elif msg.message_type in (MessageType.PRIVATE_FEEDBACK, ):
            self.action_feedback.append((self._msg_idx, Prompt(ASST, msg.ai_repr())))
        elif msg.message_type in (MessageType.PRIVATE_MESSAGE, ):
            self.action_feedback.append((self._msg_idx, Prompt(USER, msg.ai_repr())))
        else:
            print(f"Dropping message: {msg}")


class ChatGPTBot:
    """
    Mafia-playing ChatGPT bot interface
    """

    def __init__(self, name: str, role_name: str, debug: bool = True) -> None:
        self.name = name
        self.role_name = role_name.replace(' ', '')
        self.role = RoleFactory({}).create_by_name(self.role_name)
        if self.role is None:
            raise ValueError(f"Unknown role {self.role_name}")
        self.debug = debug
        self._context = ChatContext(name, self.role_name)
        self.log = logging.Logger(f"ChatGPT-{name}")
        self.log.addHandler(log.ch)

        self._handlers: T.Dict[BotAction, T.Callable[[T.List[str]], T.List[str]]] = dict()

        # outbound messages to the game get stacked here
        self._outbound_queue: asyncio.Queue = asyncio.Queue()

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        self._handlers[BotAction.DAY_ACTION] = self._resolve_day_action
        self._handlers[BotAction.NIGHT_ACTION] = self._resolve_night_action
        self._handlers[BotAction.TRIAL_VOTE] = self._resolve_trial_vote
        self._handlers[BotAction.LYNCH_VOTE] = self._resolve_lynch_vote

    def _resolve_default(self, *args, **kwargs) -> T.List[T.Optional[str]]:
        return []

    def get_action_handler(self, bot_action: BotAction) -> T.Callable[[T.List[str]], T.List[str]]:
        return self._handlers.get(bot_action, self._resolve_default)

    def _resolve_day_action(self, options: T.List[str]) -> T.List[str]:
        decision = self.make_decision(
            context=f"You are a {self.role_name}. Your ability is to {self.role.day_action_description()}.",
            choices=options,
            summary=f"You used {self.role_name}'s ability to target {{choice}}"
        )
        if decision:
            return [decision]
        return []

    def _resolve_night_action(self, options: T.List[str]) -> T.List[str]:
        decision = self.make_decision(
            context=f"You are a {self.role_name}. Your ability is to {self.role.night_action_description()}.",
            choices=options,
            summary=f"You used {self.role_name}'s ability to target {{choice}}"
        )
        if decision:
            return [decision]
        return []

    def _resolve_trial_vote(self, options: T.List[str]) -> T.List[str]:
        decision = self.make_decision(
            context=f"You are choosing whether to put someone on Trial. You may choose to not put anyone on trial.",
            choices=options,
            summary=f"You voted to put {{choice}} on trial."
        )
        if decision:
            return [decision]
        return []

    def _resolve_lynch_vote(self, options: T.List[str]) -> T.List[str]:
        decision = self.make_decision(
            # i am so curious what if we don't provide context at all
            context=f"You are choosing whether or not to lynch",
            choices=options,
            summary=f"You voted {{choice}} to lynch",
        )
        if decision:
            return [decision]
        return []

    def make_decision(self, context: str, choices: T.List[str], summary: str) -> T.Optional[str]:
        """
        Have ChatGPT make a decision for you

        A context is provided to run the command with and a summary string template
        is provided to summarize the action. The choice target should be in there.
        The keyword to use is `choice`.

        TODO: i'm not sure if we want the original prompt in action context or not...
        Honestly we probably need it, so it shouldn't be ephemeral
        """
        prompt = self.prompt_for_decision(context, choices)
        with self._context.ephemeral(prompt):
            raw_choice = self.interact()
        for choice in choices:
            if choice in raw_choice:
                break
        else:
            self.log.info(f"Warning: could not pick an exact from `{raw_choice}`.")
            return None
        self._context.action_feedback.append((self._context._msg_idx, Prompt(role=ASST, content=summary.format(choice=choice))))
        return choice

    async def iter_conversation(self) -> str:
        """
        Get the next thing to say

        Grab the current conversation history and append it to the chat context.
        Issue the request to get some output.
        """
        # wait for there to be a new entry to the conversation
        #await self._context._conversation.has_update.wait()
        print('in iter convo')
        with self._context.conversation():
            print('in iter convo inner')
            return await self.ainteract()

    def make_speech(self, context: str = "") -> str:
        prompt = self.prompt_for_speech(context)
        with self._context.ephemeral(prompt):
            self.interact()

    def prompt_for_speech(self, context: str) -> str:
        return f"{context}. You may choose to share any information or insights you have, but you do not have to. " \
            f"If you do not wish to speak, respond with 'NA'.\n" \
            f"{self.name}: "

    def prompt_for_decision(self, context: str, choices: T.List[str]) -> str:
        return f"{context}. You must choose between: " + ', '.join(choices) + \
            ". Reply in the form of 'I choose: ' followed by your choice.\n"

    # create a bunch of resolvers for each action?
    def resolve(self, options: T.List[str], count: int = 1) -> T.List[T.Any]:
        """
        Get targets
        """
        # if we need a response now, this is synchronous
        # we don't want to block while a synchronous call runs though, so i think
        # we probably need to make this asynchronous?
        #await self.ainteract()

    async def ainteract(self) -> str:
        if self.debug:
            return "(MOCK ASYNC) ChatGPT output"

        response = await openai.ChatCompletion.acreate(model=MODEL, messages=self._context.messages)
        if not response.choices:
            self.log.info("WARNING: no response gathered from ChatGPT")
            return

        response_str = response.choices[0].message.content

        self._context.record_response(response_str)

        return response_str

    def interact(self) -> str:
        if self.debug:
            return "(MOCK) ChatGPT output"

        self.log.info(f"Making request with the following context:\n{self._context.messages}")
        response = openai.ChatCompletion.create(model=MODEL, messages=self._context.messages)
        self.log.info(f"ChatGPT Response follows:\n{response}")
        if not response.choices:
            self.log.warn("WARNING: no response gathered from ChatGPT")
            return

        response_str = response.choices[0].message.content

        self._context.record_response(response_str)

        return response_str

    async def maybe_roll_over_conversation(self, force: bool = False) -> None:
        if not force and self._context._conversation.length < 300:
            return
        digest = await self._context.roll_over_conversation()
        #self._context.

    def ingest(self, message: "Message") -> None:
        """
        Depending on what kind of message we get, handle it appropriately.
        """
        self._context.update(message)

    def ingest_proto(self, message: message_pb2.Message) -> None:
        self._context.update_with_proto(message)


async def test():
    ctx = ChatContext("Albert", "Godfather")
    convo = Conversation(ctx)
    convo.add_string_message("chilly mango: 'HOLY MOLY BRO'")
    convo.add_string_message("chilly mango: 'i found the godfather'")
    convo.add_string_message("chilly mango: 'it is Albert'")
    convo.add_string_message("Albert: 'i am not the Godfather'")
    res = await convo.digest(debug=False)
    print(res)


if __name__ == "__main__":
    asyncio.run(test())
