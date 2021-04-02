from abc import ABC
from abc import abstractmethod


class MetaTaskInterface(ABC):
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
        """ If task allows actions to be taken, return here."""
        pass

    @abstractmethod
    def _requested_action(self, github_body) -> bool:
        """Logic to execute when a user requests an action on the task"""
        raise NotImplementedError("Please implement _requested_action.")

    @abstractmethod
    def _execute(self, github_body) -> bool:
        """Logic to execute for task"""
        raise NotImplementedError("Please implement _execute method.")
