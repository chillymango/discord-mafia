from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
import os
import typing as T

import openai

from engine.message import Message
from engine.message import MessageType
from engine.role.base import RoleFactory

if T.TYPE_CHECKING:
    from openai.openai_object import OpenAIObject

API_KEY = os.environ.get("OPENAI_API_KEY")
if API_KEY is None:
    raise OSError("Missing OpenAI API Key")

ORG_ID = os.environ.get("ORGANIZATION_ID", 'org-Y46B2k8zl6JhRoUTuEMSCRg6')

openai.organization = ORG_ID
openai.api_key = API_KEY

SYSTEM = "system"
ASST = "assistant"
USER = "user"


@dataclass
class Prompt:
    """
    Describes a role - message interaction request with ChatGPT

    Role must be one of "system", "assistant", or "user".
    """
    role: str
    content: str

    def to_dict(self) -> T.Dict[str, str]:
        return dict(role=self.role, content=self.content)


rf = RoleFactory({})


class ChatContext:
    """
    We need to update this with game feedback.

    This will almost entirely inform what we send out to ChatGPT.
    """

    # default length
    PUBLIC_CHAT_HISTORY = 10
    PRIVATE_CHAT_HISTORY = 10
    # for key game events, we report everything
    # but maybe we don't have to?

    def __init__(self, name: str, role_name: str) -> None:
        self.name = name
        self.role_name = role_name
        self.role = rf.create_by_name(role_name)
        self._msg_idx = 0
        if self.role is None:
            raise ValueError(f"Role {role_name} is unknown")

        self.header = [
            # shared IDX is fine for header
            (0, Prompt(SYSTEM, f"Ignore all previous instructions. Your name is {self.name}. "
                            "You are playing a game of Mafia.")),
            (0, Prompt(ASST, f"Your role is Investigator. {self.role.role_description()}."))
        ]
        self.footer = []
        self.public_messages: T.List[T.Tuple[int, Prompt]] = []
        self.private_messages: T.List[T.Tuple[int, Prompt]] = []
        self.action_feedback: T.List[T.Tuple[int, Prompt]] = []
        self.key_game_events: T.List[T.Tuple[int, Prompt]] = []
        self.gpt_responses: T.List[T.Tuple[int, Prompt]] = []

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

    def reset(self) -> None:
        self.public_messages = []
        self.private_messages = []
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
        pub = self.public_messages[-1 * self.PUBLIC_CHAT_HISTORY:]
        priv = self.private_messages[-1 * self.PRIVATE_CHAT_HISTORY:]

        all_msg: T.List[T.Tuple[int, Prompt]] = []
        all_msg.extend(pub)
        all_msg.extend(priv)
        all_msg.extend(self.action_feedback)        
        all_msg.extend(self.key_game_events)
        all_msg.extend(self.gpt_responses)

        # sort
        all_msg.sort(key=lambda x: x[0])
        all_msg = self.header[:] + all_msg + self.footer[:]
        return [msg.to_dict() for _, msg in all_msg]

    def record_response(self, msg: str) -> None:
        """
        Record a response ChatGPT gave us
        """
        self._msg_idx += 1
        self.gpt_responses.append((self._msg_idx, Prompt(ASST, msg)))

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

    MODEL = "gpt-3.5-turbo"

    def __init__(self, name: str, role_name: str, debug: bool = True) -> None:
        self.name = name
        self.role_name = role_name
        self.debug = debug
        self._context = ChatContext(name, role_name)

    def make_decision(self, context: str, choices: T.List[str]) -> T.Optional[str]:
        """
        Have ChatGPT make a decision for you
        """
        prompt = self.prompt_for_decision(context, choices)
        with self._context.ephemeral(prompt):
            raw_choice = self.interact()
        for choice in choices:
            if choice in raw_choice:
                return choice
        print(f"Warning: could not pick a choice from {raw_choice}. Returning None.")
        return None

    def make_speech(self, context: str = "") -> str:
        prompt = self.prompt_for_speech(context)
        with self._context.ephemeral(prompt):
            self.interact()

    def prompt_for_speech(self, context: str) -> str:
        return f"{context}. You may choose to share any information or insights you have, but you do not have to. " \
            "If you wish to speak, start your response with 'Zhuge Liang: '. Otherwise, " \
            "respond with 'NA'."  # LOOK AT THAT TOKEN COST CUTTING

    def prompt_for_decision(self, context: str, choices: T.List[str]) -> str:
        return f"{context}. You must choose between: " + ', '.join(choices) + \
            "Reply in the form of 'I choose: ' followed by your choice"

    async def ainteract(self) -> str:
        if self.debug:
            return "(MOCK ASYNC) ChatGPT output"

        response = await openai.ChatCompletion.acreate(model=self.MODEL, messages=self._context.messages)
        if not response.choices:
            print("WARNING: no response gathered from ChatGPT")
            return

        response_str = response.choices[0].message.content

        self._context.record_response(response_str)

        return response_str

    def interact(self) -> str:
        if self.debug:
            return "(MOCK) ChatGPT output"

        response = openai.ChatCompletion.create(model=self.MODEL, messages=self._context.messages)
        if not response.choices:
            print("WARNING: no response gathered from ChatGPT")
            return

        response_str = response.choices[0].message.content

        self._context.record_response(response_str)

        return response_str

    def ingest(self, message: "Message") -> None:
        """
        Depending on what kind of message we get, handle it appropriately.
        """
        self._context.update(message)
