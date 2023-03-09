from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Annotated, List, Any, Optional, Union, Literal
from os.path import exists
from enum import Enum

MIN_MEMORY=512
MIN_STORAGE=512
DEFAULT_TIMEOUT=60

class SubscriptionLevels:
    FREE = 0
    STARTUP = 1
    GROWTH = 2
    ENTERPRISE = 3


# List of Capabilities that tasks are able to add
class GithaxsWorker(BaseModel):
    enabled: bool = Field(False, description="Githaxs worker capability")
    event_name: str = Field("githaxs-worker", description="Name of event for task to subscribe to (i.e. task_name.worker)")

class MainBranchAnalysis(BaseModel):
    enabled: bool = Field(False, description="Enables tasks to run analysis on the main branch of a repo on a push event.")

class TaskSettings(BaseModel):
    enabled: bool = Field(False, description="Set to true if task has user settings.")

class TaskOrchestrator(BaseModel):
    enabled: bool = Field(False, description="Set to true if task is an orchestrator of worker tasks.")

class AssumeIAMRole(BaseModel):
    enabled: bool = Field(False, description="Set to true if task needs to assume IAM role in another AWS Account.")
    role_arn: str = Field(None, description="Role ARN to be assumed. If set here a user will not be able to override it with task parameters. Used for internal Githaxs tasks.")
    inject_ssm_parameters: Optional[bool] = Field(False, description="Set to true if task will inject SSM parameters from AWS Account.")

class DockerBuild(BaseModel):
    enabled: bool = Field(False, description="Set to true if task needs to to build docker images.")

class Checkout(BaseModel):
    enabled: bool = Field(False, description="Set to true if task needs to clone the repo.")
    depth: Optional[int] = Field(1, description="Clone depth. Set to 0 for full clone.")
    include_files_changed: Optional[bool] = Field(False, description="Set to true if task needs to include files changed in the pull request.")

class Action(BaseModel):
    label: str
    identifier: str
    description: str

class CheckRun(BaseModel):
    """Adding this capability will enable a task to report results to Check Runs."""
    enabled: bool = Field(False, description="Set to true if task uses Check Runs.")
    # Pull Request authors to avoid for checks (i.e. always return passing)
    ignored_authors: Optional[List[str]] = []
    # Return passing check if branch or topic has hotfix in the name
    allow_hotfix: Optional[bool] = False
    # A task can fix some of the issues it finds
    fix_errors: Optional[bool] = False
    # Allow task to handle its own check run by injecting a client into the task
    custom: Optional[bool] = False
    # Actions the user can invoke from the GitHub UI
    actions: Optional[List[Action]] = []

    @validator("actions", always=True)
    def _validate_actions(cls, v, values, **kwargs):
        if values['fix_errors'] is True:
            v.append(
                Action(
                    label='Fix',
                    identifier='fix',
                    description='Fix issues shown below.'
                )
            )

        if values['allow_hotfix'] is True:
            v.append(
                Action(
                    label='Hotfix',
                    identifier='hotfix',
                    description='Force check to pass for hotfix.'
                )
            )

        assert len(v) <= 3
# End of capabilities

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

class Command(BaseModel):
    title: str
    slug: str
    command: str
    check: bool
    fail_message: Optional[str]
    run_on_fail: Optional[bool] = False
    include_output: Optional[bool] = True
    # This value is used to determine if the output of the command should
    # update the env for future commands.
    include_in_env: Optional[str] = None
    completed: bool = False
    duration: Optional[float] = None
    exit_code: Optional[int]
    output: Optional[str] = None

class Capabilities(BaseModel):
    githaxs_worker: GithaxsWorker = Field(GithaxsWorker())
    task_settings: TaskSettings = Field(TaskSettings())
    task_orchestrator: TaskOrchestrator = Field(TaskOrchestrator())
    assume_iam_role: AssumeIAMRole = Field(AssumeIAMRole())
    docker_build: DockerBuild = Field(DockerBuild())
    checkout: Optional[Checkout] = Field(Checkout())
    check_run: CheckRun = Field(CheckRun())
    main_branch_analysis: MainBranchAnalysis = Field(MainBranchAnalysis())

class RunnerId(str, Enum):
    PYTHON_3_10 = 'python_3_10'
    NODE_16 = 'node_16'

class Task(BaseModel):
    version: str = Field(default=2, const=True)
    name: str
    capabilities: Optional[Capabilities] = Field(Capabilities())
    slug: str = None
    summary: str
    description: str
    beta: bool = True
    subscription_level: int = SubscriptionLevels.FREE
    parameters: Optional[List[Parameter]] = []
    has_public_repo: Optional[bool] = True
    show: str = 'all'  # all | owner | admin | none
    default_configuration: Optional[DefaultConfiguration]
    tags: Optional[List[str]] = []
    platform: Optional[str] = Field('arm64', const=True)
    owner: Optional[str] = Field('githaxs', const=True)  # GitHub org that created the task
    hosting_option: Optional[str] = Field('saas', const=True)
    subscribed_events: Optional[List[str]] = []
    extra_sam_resources: Optional[List[str]] = []
    commands: List[Command] = Field(..., description="List of commands for task to execute")
    runner_id: RunnerId

    @validator("slug", always=True)
    def create_slug(cls, v, values, **kwargs):
        return values['name'].lower().replace(' ', '-')

    def validate(self):
        assert self.capabilities.check_run.enabled and self.capabilities.main_branch_analysis.enabled is False, "A task cannot work on check runs and main branch analysis at the same time"
        return True

    # TODO: fix this up
    @validator("parameters", always=True)
    def _validate_parameters(cls, v, values, **kwargs):
        if values['capabilities'].assume_iam_role.enabled:
            v.parameters.append(
                Parameter(
                    name='iam_role_arn',
                    description='AWS IAM role ARN to assume',
                    default=None,
                    type='string',
                    required=True
                )
            )

            if values['capabilities'].assume_iam_role.inject_ssm_parameters:
                v.parameters.append(
                    Parameter(
                        name='ssm_prefix',
                        description='Prefix path of SSM parameters to inject into environment (i.e. /prod/',
                        default=None,
                        type='string',
                        required=True))
        return v

    def get_subscribed_events(self):
        events = self.subscribed_events
        if self.capabilities.check_run.enabled:
            events += [
                'pull_request.opened',
                'pull_request.reopened',
                'pull_request.synchronize',
                'check_run.rerequested',
            ]
        if self.capabilities.check_run.actions is not None:
            events += ['check_run.requested_action']

        if self.capabilities.main_branch_analysis.enabled:
            events += ['push']

        if self.capabilities.githaxs_worker.enabled:
            events += [self.capabilities.githaxs_worker.event_name]

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
            'capabilities': self.capabilities,
            'subscribed_events': self.get_subscribed_events(),
            'default_configuration': self.default_configuration.dict(),
        }
