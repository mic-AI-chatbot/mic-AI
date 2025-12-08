import logging
import configparser
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    An abstract base class for all tools.

    This class provides common functionality for all tools, including:
    - Loading configuration from a file.
    - Setting up a logger.
    """

    def __init__(self, tool_name: str, config_file: str = 'tools/config.ini', **kwargs):
        """
        Initializes the BaseTool.

        Args:
            tool_name: The name of the tool.
            config_file: The path to the configuration file.
        """
        self.tool_name: str = tool_name
        self.config: configparser.ConfigParser = self._load_config(config_file)
        self.logger: logging.Logger = self._setup_logging()
        self.is_publishable: bool = kwargs.get('is_publishable', False)
        self.requires_advanced_knowledge: bool = kwargs.get('requires_advanced_knowledge', False)

    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """
        Loads the configuration from the specified file.

        Args:
            config_file: The path to the configuration file.

        Returns:
            A ConfigParser object.
        """
        config = configparser.ConfigParser()
        try:
            config.read(config_file)
        except configparser.Error as e:
            print(f"Could not load or parse config file {config_file}: {e}")
            config['DEFAULT'] = {'model_name': 'distilgpt2'}
        return config

    def _setup_logging(self) -> logging.Logger:
        """
        Sets up the logger for the tool.

        Returns:
            A Logger object.
        """
        logger = logging.getLogger(self.tool_name)
        log_level = self.config.get('DEFAULT', 'log_level', fallback='INFO').upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    @property
    @abstractmethod
    def description(self) -> str:
        """
        A description of the tool's purpose.
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        A dictionary defining the tool's parameters in a JSON Schema-like format.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Dict[str, Any]) -> Any:
        """
        Executes the tool's main functionality.

        This method must be implemented by any concrete tool that inherits from BaseTool.
        """
        pass
