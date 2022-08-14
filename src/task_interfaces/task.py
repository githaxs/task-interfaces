from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated, List, Any, Optional, Union, Literal
from os.path import exists


class SubscriptionLevels:
    FREE = 0
    STARTUP = 1
    GROWTH = 2
    ENTERPRISE = 3


# List of Capabilities that tasks are able to add
class GithaxsWorker(BaseModel):
    type: Literal["githaxs-worker"]


class InjectSettingsCapability(BaseModel):
    type: Literal["inject-settings"]


class AssumeIAMRoleCapability(BaseModel):
    type: Literal["aws-assume-iam-role"]
    inject_ssm_parameters: Optional[bool] = False


class MainBranchAnalysisCapability(BaseModel):
    type: Literal["main-branch-analysis"]


class DockerBuildCapability(BaseModel):
    type: Literal["docker-build"]


class CheckoutCapability(BaseModel):
    """Adding this capability will clone the repository."""
    type: Literal["checkout"]
    depth: Optional[int] = 1  # How many commits to clone


class Action(BaseModel):
    label: str
    identifier: str
    description: str


class CheckRunCapability(BaseModel):
    """Adding this capability will enable a task to report results to Check Runs."""
    type: Literal["checkrun"]
    # Actions the user can invoke from the GitHub UI
    actions: Optional[List[Action]] = []
    # Pull Request authors to avoid for checks (i.e. always return passing)
    ignored_authors: Optional[List[str]]
    # Return passing check if branch or topic has hotfix in the name
    allow_hotfix: Optional[bool] = False
    # A task can fix some of the issues it finds
    fix_errors: Optional[bool] = False

# End of capabilities


CapabilityItem = Annotated[
    Union[
        GithaxsWorker,
        DockerBuildCapability,
        InjectSettingsCapability,
        AssumeIAMRoleCapability,
        MainBranchAnalysisCapability,
        CheckRunCapability,
        CheckoutCapability, ],
    Field(discriminator="type")
]

# Packages


class Packages(BaseModel):
    python: List[str] = []
    system: List[str] = []
    node: List[str] = []
    ruby: List[str] = []
    custom: List[str] = []

# Task Properties


class ParameterTypes(str, Enum):
    STRING = 'string'
    SECRET = 'secret'
    BOOLEAN = 'boolean'


class Parameter(BaseModel):
    name: str
    description: str
    default: Optional[Any] = None
    type: Optional[ParameterTypes]
    required: Optional[bool] = False


class Installation(BaseModel):
    org: Optional[bool] = False
    repo_languages: Optional[List[str]] = []


class DefaultConfiguration(BaseModel):
    installation: Installation
    settings: Optional[Any]


class Task(BaseModel):
    name: str
    summary: str
    description: str
    beta: bool = True
    capabilities: Optional[List[CapabilityItem]]
    subscription_level: int = 0
    runtime: str
    parameters: Optional[List[Parameter]] = []
    has_public_repo: Optional[bool] = True
    memory: int = 512
    timeout: int = 60
    storage: int = 512
    show: str = 'all'  # all | owner | admin | none
    default_configuration: Optional[DefaultConfiguration]
    tags: Optional[List[str]] = []
    packages: Optional[Packages]
    owner: Optional[str] = 'githaxs'  # GitHub org that created the task
    # saas | self_hosted -> For future use when we allow tasks to be hosted on
    # client infrastructure
    hosting_option: Optional[str] = 'saas'
    subscribed_events: Optional[List[str]] = []

    @property
    def slug(self):
        return self.name.lower().replace(' ', '-')

    def __check_for_capability(self, capability):
        if self.capabilities is None:
            return False

        return any([isinstance(x, capability) for x in self.capabilities])

    def __get_capability(self, capability):
        return next(
            (x for x in self.capabilities if isinstance(
                x, capability)), None)

    def has_check_run_capability(self):
        return self.__check_for_capability(CheckRunCapability)

    def has_main_branch_capability(self):
        return self.__check_for_capability(MainBranchAnalysisCapability)

    def has_githaxs_worker_capability(self):
        return self.__check_for_capability(GithaxsWorker)

    def has_aws_iam_assume_role_capability(self):
        return self.__check_for_capability(AssumeIAMRoleCapability)

    def has_inject_ssm_parameters_capability(self):
        if not self.has_aws_iam_assume_role_capability():
            return False
        capability = self.__get_capability(AssumeIAMRoleCapability)

        return capability.inject_ssm_parameters

    def has_docker_build_capability(self):
        return self.__check_for_capability(DockerBuildCapability)

    def allows_for_hotfixes(self):
        if not self.__check_for_capability(CheckRunCapability):
            return False
        capability = self.__get_capability(CheckRunCapability)

        return capability.allow_hotfix

    def get_checkout_depth(self):
        capability = self.__get_capability(CheckoutCapability)
        return capability.depth

    def ignored_authors(self):
        if not self.__check_for_capability(CheckRunCapability):
            return []
        capability = self.__get_capability(CheckRunCapability)

        return capability.ignored_authors

    def get_check_run_actions(self):
        if not self.has_check_run_capability():
            return None

        capability = self.__get_capability(CheckRunCapability)
        actions = capability.actions
        if actions is None:
            return None

        if capability.fix_errors is True:
            actions.append(Action(
                label='Fix',
                identifier='fix',
                description='Fix issues shown below.'
            ))

        if capability.allow_hotfix is True:
            actions.append(Action(
                label='Hotfix',
                identifier='hotfix',
                description='Force check to pass for hotfix.'
            ))

        if len(actions) == 0:
            return None

        return [x.dict() for x in actions]

    def has_inject_settings_capability(self):
        return self.__check_for_capability(InjectSettingsCapability)

    def has_checkout_capability(self):
        return self.__check_for_capability(CheckoutCapability)

    def has_main_branch_capability(self):
        return self.__check_for_capability(MainBranchAnalysisCapability)

    def validate(self):
        if self.runtime == 'bash':
            if not exists("./task.sh"):
                print(
                    "task.sh must exist for runtime=bash and it must have a run function.")
                exit(1)
        elif self.runtime == 'python':
            if not exists("./task.py"):
                print(
                    "task.py must exist for runtime=python and it must have a run function.")
                exit(1)

        if self.runtime == 'bash' and not self.has_checkout_capability():
            print("Bash script tasks can only be used with cloned repos. Please add checkout capability or use python runtime.")
            exit(1)

    def get_parameters(self):
        if self.parameters is None:
            self.parameters = []
        if self.__check_for_capability(AssumeIAMRoleCapability):
            self.parameters.append(
                Parameter(
                    name='iam_role_arn',
                    description='AWS IAM role ARN to assume',
                    default=None,
                    type='string',
                    required=True
                )
            )

        if self.has_inject_ssm_parameters_capability():
            self.parameters.append(
                Parameter(
                    name='ssm_prefix',
                    description='Prefix path of SSM parameters to inject into environment (i.e. /prod/',
                    default=None,
                    type='string',
                    required=True))
        return [x.dict() for x in self.parameters]

    def get_subscribed_events(self):
        events = self.subscribed_events
        if self.has_check_run_capability():
            events += [
                'pull_request.opened',
                'pull_request.reopened',
                'pull_request.synchronize',
                'check_run.rerequested',
            ]
        if self.get_check_run_actions() is not None:
            events += ['check_run.requested_action']

        if self.has_main_branch_capability():
            events += ['push']

        if self.has_githaxs_worker_capability():
            events += ['githaxs']

        return events

    def to_json(self):
        return {
            'name': self.name,
            'slug': self.slug,
            'summary': self.summary,
            'description': self.description,
            'memory': self.memory,
            'timeout': self.timeout,
            'storage': self.storage,
            'subscription_level': self.subscription_level,
            'parameters': self.get_parameters(),
            'show': self.show,
            'tags': self.tags,
            'capabilities': [
                x.dict() for x in self.capabilities] if self.capabilities is not None else None,
            'subscribed_events': self.get_subscribed_events(),
            'default_configuration': self.default_configuration.dict(),
        }
