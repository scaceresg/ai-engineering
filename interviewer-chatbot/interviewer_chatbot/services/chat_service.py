"""Chat service for streaming interview responses."""

from collections.abc import Iterator

from langchain_openai import ChatOpenAI


class ChatService:
    """Stateless wrapper around a ChatOpenAI client for streaming interview turns.

    All conversation state is managed by the caller (Streamlit session_state).
    This class is safe to share across concurrent sessions.

    Args:
        client: Pre-configured ChatOpenAI instance to use for inference.
    """

    def __init__(self, client: ChatOpenAI) -> None:
        self._client = client

    def stream_response(self, messages: list[dict]) -> Iterator[str]:
        """Stream a response token by token for the given conversation.

        Args:
            messages: Full conversation history as a list of role/content dicts,
                including the system prompt at index 0.

        Yields:
            Text chunks from the model as they arrive.
        """
        stream = self._client.stream(messages)
        yield from (str(chunk.content) for chunk in stream)
