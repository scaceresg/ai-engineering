"""
Application configuration loader.
"""

import os
from importlib.resources import files

import yaml

from interviewer_chatbot.utils.logger import logger

DEFAULT_CONFIG_PATH = "configs"
DEFAULT_ENV_VAR = "APP_ENV"


class Config:
    """
    Hierarchical YAML configuration manager.

    Loads a base config file and merges an environment-specific override into
    it. The merge is recursive: nested dicts are merged key-by-key rather than
    replaced wholesale.

    Args:
        environment: Name of the active environment (e.g. ``"local"``,
            ``dev``,``"stg"``, ``"prod"``). Defaults to the value of the
            ``APP_ENV`` environment variable, or ``"default"`` if unset.
    """

    def __init__(self, environment: str | None = None) -> None:
        self._environment = environment or os.environ.get(DEFAULT_ENV_VAR, "default")
        self._vars: dict | None = None

    @property
    def env_vars(self) -> dict:
        """Return the merged configuration, loading it lazily on first access."""
        if self._vars is None:
            self._vars = self._load_config()
        return self._vars

    def load_config_from_file(self, path: str) -> dict:
        """
        Read and parse a YAML file from the configs package directory.

        Args:
            path: Filename relative to ``DEFAULT_CONFIG_PATH`` (e.g.
                ``"environment.yaml"``).

        Returns:
            Parsed YAML content as a plain ``dict``, or an empty ``dict``
            when the file does not exist.

        Raises:
            yaml.YAMLError: If the file exists but cannot be parsed.
            Exception: For any other unexpected I/O error.
        """
        try:
            raw = files(DEFAULT_CONFIG_PATH).joinpath(path).read_text(encoding="utf-8")
        except FileNotFoundError as e:
            logger.warning("Config file not found at %s/%s: %s", DEFAULT_CONFIG_PATH, path, e)
            return {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing config file {DEFAULT_CONFIG_PATH}/{path}: {e}") from e
        except Exception as e:
            raise Exception(f"Unexpected error loading config file {DEFAULT_CONFIG_PATH}/{path}: {e}") from e

        return yaml.load(raw, Loader=yaml.SafeLoader) or {}

    def _load_config(self) -> dict:
        """Load the base config and merge the environment override on top."""
        base = self.load_config_from_file("environment.yaml")

        env_filename = "environment.yaml" if self._environment == "default" else f"environment-{self._environment}.yaml"
        override = self.load_config_from_file(env_filename)

        if override:
            base = self._merge(base, override, path="")

        return base

    def _merge(self, base: dict, override: dict, *, path: str) -> dict:
        """
        Recursively merge *override* into *base*, returning the result.

        When both dicts contain the same key:
        - If both values are dicts, the merge recurses into them.
        - Otherwise the override value wins and a warning is logged so
          the conflict is visible without being fatal.

        Args:
            base: The base configuration dictionary.
            override: The environment-specific overrides to apply.
            path: Dot-separated key path used in warning messages to
                pinpoint where a conflict occurred (e.g. ``"llm.model"``).

        Returns:
            A new ``dict`` with *override* values merged into *base*.
        """
        merged = dict(base)

        for key, override_value in override.items():
            key_path = f"{path}.{key}" if path else key

            if key not in merged:
                merged[key] = override_value
                continue

            base_value = merged[key]

            if isinstance(base_value, dict) and isinstance(override_value, dict):
                merged[key] = self._merge(base_value, override_value, path=key_path)
            else:
                if base_value != override_value:
                    logger.warning(
                        "Config conflict at '%s': base=%r overridden by env=%r",
                        key_path,
                        base_value,
                        override_value,
                    )
                merged[key] = override_value

        return merged
