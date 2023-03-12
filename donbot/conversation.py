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