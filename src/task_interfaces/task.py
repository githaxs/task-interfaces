import re
from abc import ABC
from abc import abstractmethod
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict


class TaskTypes(Enum):
    CODE_FORMAT = "code_format"
    CODE_ANALYSIS = "code_analysis"
    WORKFLOW = "workflow"
    DEPLOY_WORKFLOW = "deploy_workflow"
    DEPLOY_WORKER = "deploy_worker"
    DEPLOY = "deploy"
    UNIT_TEST = "unit_test"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class DeployTaskInterface(ABC):
    type = TaskTypes.DEPLOY
    requires_dependencies = False

    def __init__(self):
        if self.subscription_level not in [0, 1, 2, 3]:
            raise Exception("Subscription Level is not a valid value.")

    @property
    @abstractmethod
    def name(self):
        """Returns the name of the task."""
        pass

    @property
    def slug(self):
        """Retuns the slug of the task."""
        return self.name.lower().replace(' ', '-')

    @property
    @abstractmethod
    def subscription_level(self) -> int:
        pass

    def pre_execute_hook(self, **kwargs):
        pass


class SubscriptionLevels:
    FREE = 0
    STARTUP = 1
    GROWTH = 2
    ENTERPRISE = 3


class BaseTask(BaseModel):
    name: str
    subscription_level: int

    @property
    def slug(self):
        """Retuns the slug of the task."""
        return self.name.lower().replace(' ', '-')


class WorkflowTask(BaseTask):
    actions: List[Dict]
    type: str = TaskTypes.WORKFLOW
    pass_summary: str = ""

    @abstractmethod
    def execute(self, github_body) -> bool:
        """Logic to execute for task"""
        raise NotImplementedError("Please implement execute method.")


class FormatTask(BaseTask):
    can_fix: bool = True
    type = TaskTypes.CODE_FORMAT
    source_script_path: str
    handler: str = "task"

    def pre_execute_hook(self, settings):
        pass


class StaticAnalysisTask(FormatTask):
    can_fix: bool = False


class CodeAnalysisTask(BaseTask):
    type = TaskTypes.CODE_ANALYSIS
    source_script_path: str
    handler: str = "task"

    def pre_execute_hook(self, settings):
        pass


class TaskInterface(ABC):
    command: str = ""
    source_script_path: str = ""
    handler: str = ""

    def __init__(self):
        if self.subscription_level not in [0, 1, 2, 3]:
            raise Exception("Subscription Level is not a valid value.")

        if self.type not in TaskTypes.__members__.values():
            raise Exception("Task Type is not a valid value.")

        if self.type != TaskTypes.WORKFLOW:
            if not self.command and not self.source_script_path and not self.handler:
                raise Exception(
                    "Either command or source script and handle must be defined."
                )

            if (self.source_script_path and not self.handler) or (
                not self.source_script_path and self.handler
            ):
                raise Exception(
                    "Source script and handler must be used together.")

            if not re.match(r"[a-z-]+", self.slug):
                raise Exception("Task Slug can only contain letters and -.")

    @property
    @abstractmethod
    def name(self):
        """Returns the name of the task."""
        pass

    @property
    def slug(self):
        """Retuns the slug of the task."""
        return self.name.lower().replace(' ', '-')

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

    def pre_execute_hook(self, **kwargs):
        pass
