"""API key loading: python-dotenv for local, GCP Secret Manager for dev."""

import os

from interviewer_chatbot.utils.logger import logger


def load_secrets(environment: str) -> None:
    """Populate OPENAI_API_KEY from the appropriate source for the environment.

    This is a no-op when the variable is already set (e.g. injected by the
    container runtime or a previous call).

    Args:
        environment: Active environment name (``"local"`` or ``"dev"``).
            - ``local``  — reads from a ``.env`` file via python-dotenv.
            - any other — fetches from GCP Secret Manager using coordinates
              read from the environment-specific YAML config file.
    """
    if os.environ.get("OPENAI_API_KEY"):
        logger.debug("OPENAI_API_KEY already set; skipping secret load")
        return

    if environment == "local":
        _load_from_dotenv()
    else:
        from interviewer_chatbot.utils.config import Config

        cfg = Config(environment=environment).env_vars
        _load_from_secret_manager(
            project_id=cfg["project-id"],
            secret_name=cfg["secret-name"],
        )


def _load_from_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Loaded secrets from .env (local)")
    except ImportError:
        logger.warning("python-dotenv not installed; skipping .env load")


def _load_from_secret_manager(project_id: str, secret_name: str) -> None:
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    resource = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

    response = client.access_secret_version(request={"name": resource})
    secret_value = response.payload.data.decode("UTF-8")

    os.environ["OPENAI_API_KEY"] = secret_value
    logger.info("Loaded OPENAI_API_KEY from Secret Manager (%s)", secret_name)
