"""
Configuration Manager for MCP CalDAV Application
Handles loading and managing application configuration.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration from multiple sources."""

    def __init__(self, config_file: str = "config/settings.json"):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file and environment variables.

        Returns:
            Dictionary containing all configuration values
        """
        config = {}

        # Load from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load configuration from file: {e}")

        # Override with environment variables
        env_config = self._load_from_env()
        config.update(env_config)

        # Set defaults if not provided
        self._set_defaults(config)

        return config

    def _load_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Returns:
            Dictionary with environment variable configurations
        """
        config = {}

        # CalDAV server settings
        if "CALDAV_SERVER_URL" in os.environ:
            config["server_url"] = os.environ["CALDAV_SERVER_URL"]
        if "CALDAV_USERNAME" in os.environ:
            config["username"] = os.environ["CALDAV_USERNAME"]
        if "CALDAV_PASSWORD" in os.environ:
            config["password"] = os.environ["CALDAV_PASSWORD"]
        if "CALDAV_USE_SSL" in os.environ:
            config["use_ssl"] = os.environ["CALDAV_USE_SSL"].lower() == "true"
        if "CALDAV_TIMEZONE" in os.environ:
            config["timezone"] = os.environ["CALDAV_TIMEZONE"]

        # Logging settings
        if "LOG_LEVEL" in os.environ:
            config["log_level"] = os.environ["LOG_LEVEL"]

        return config

    def _set_defaults(self, config: Dict[str, Any]) -> None:
        """
        Set default values for configuration options.

        Args:
            config: Configuration dictionary to update with defaults
        """
        if "server_url" not in config:
            config["server_url"] = "http://localhost:5232"
        if "username" not in config:
            config["username"] = "user"
        if "password" not in config:
            config["password"] = ""
        if "use_ssl" not in config:
            config["use_ssl"] = True
        if "log_level" not in config:
            config["log_level"] = "INFO"

    def get_timezone(self) -> str:
        return os.environ.get("CALDAV_TIMEZONE", self.config.get("timezone", "UTC"))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value

    def save(self) -> None:
        """
        Save current configuration to file.
        """
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
