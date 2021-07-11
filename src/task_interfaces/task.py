import re
from abc import ABC
from abc import abstractmethod
from enum import Enum


class SubscriptionLevels(Enum):
    FREE = 0
    STARTUP = 1
    GROWTH = 2
    ENTERPRISE = 3


class TaskTypes(Enum):
    CODE_FORMAT = "code_format"
    CODE_ANALYSIS = "code_analysis"
    META_ANALYSIS = "meta_analysis"


class TaskInterface(ABC):
    command: str = None
    source_script: str = None
    handler: str = None

    def __init__(self):
        if self.subscription_level not in SubscriptionLevels.__members__.values():
            raise Exception("Subscription Level is not a valid value.")

        if self.type not in TaskTypes.__members__.values():
            raise Exception("Task Type is not a valid value.")

        if not self.command and not self.source_script and not self.handler:
            raise Exception(
                "Either command or source script and handle must be defined."
            )

        if (self.source_script and not self.handler) or (
            not self.source_script and self.handler
        ):
            raise Exception("Source script and handler must be used together.")

        if not re.match(r"[a-z-]+", self.slug):
            raise Exception("Task Slug can only contain letters and -.")

    @property
    @abstractmethod
    def name(self):
        """Returns the name of the task."""
        pass

    @property
    @abstractmethod
    def slug(self):
        """Retuns the slug of the task."""
        pass

    @property
    @abstractmethod
    def fail_summary(self) -> str:
        """Summary to return if task fails."""
        pass

    @property
    @abstractmethod
    def fail_text(self) -> str:
        """Longer description to return if task fails."""
        pass

    @property
    @abstractmethod
    def pass_summary(self) -> str:
        """Summary to return if task passes."""
        pass

    @property
    @abstractmethod
    def pass_text(self) -> str:
        """Longer description to return if task passes."""
        pass

    @property
    @abstractmethod
    def actions(self) -> dict:
        """If task allows actions to be taken, return here."""
        pass

    @abstractmethod
    def execute(self, github_body) -> bool:
        """Logic to execute for task"""
        raise NotImplementedError("Please implement execute method.")

    @property
    @abstractmethod
    def subscription_level(self) -> int:
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        pass
