"""Feedback service for generating interview evaluation and suggestions."""

from openai import OpenAI


class FeedbackService:
    """Stateless wrapper around an OpenAI client for feedback generation.

    Invokes the model once with the full conversation transcript and returns a
    structured evaluation. This class is safe to share across concurrent sessions.

    Args:
        client: Shared OpenAI client instance.
        model_params: Per-request model parameters (model, temperature, etc.).
    """

    def __init__(self, client: OpenAI, model_params: dict) -> None:
        self._client = client
        self._model_params = model_params

    def generate_feedback(self, feedback_prompt: str, conversation_history: str) -> str:
        """Generate structured feedback for a completed interview.

        Args:
            feedback_prompt: System-level instructions that define the evaluation
                format and criteria, loaded from config at runtime.
            conversation_history: The full interview transcript as a formatted
                string (e.g. "assistant: ...\nuser: ...").

        Returns:
            A structured feedback string ready to display in the UI.
        """
        response = self._client.chat.completions.create(
            messages=[
                {"role": "system", "content": feedback_prompt},
                {"role": "user", "content": f"This is the interview you need to evaluate:\n\n{conversation_history}"},
            ],
            **self._model_params,
        )
        return response.choices[0].message.content or ""
