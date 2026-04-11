"""Chat service for streaming interview responses."""

from collections.abc import Iterator

from openai import OpenAI


class ChatService:
    """Stateless wrapper around an OpenAI client for streaming interview turns.

    All conversation state is managed by the caller (Streamlit session_state).
    This class is safe to share across concurrent sessions.

    Args:
        client: Shared OpenAI client instance.
        model_params: Per-request model parameters (model, temperature, etc.).
    """

    def __init__(self, client: OpenAI, model_params: dict) -> None:
        self._client = client
        self._model_params = model_params

    def stream_response(self, messages: list[dict]) -> Iterator[str]:
        """Stream a response token by token for the given conversation.

        Args:
            messages: Full conversation history as a list of role/content dicts,
                including the system prompt at index 0.

        Yields:
            Text chunks from the model as they arrive.
        """
        stream = self._client.chat.completions.create(messages=messages, stream=True, **self._model_params)
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
