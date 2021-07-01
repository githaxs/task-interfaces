import os
from abc import ABC
from abc import abstractmethod
from code_check import CodeCheck
from yaml import dump


class MetaTaskInterface(ABC):
    def __init__(self, name, slug, pass_summary, pass_text, fail_summary, fail_text, subscription_level):
        self.name = name
        self.slug = slug
        self.pass_summary = pass_summary
        self.pass_text = pass_text
        self.fail_summary = fail_summary
        self.fail_text = fail_text
        self.subscription_level = subscription_level

    @property
    @abstractmethod
    def name(self):
        """Returns the name of the task."""
        pass

    @name.setter
    def name(self, value):
        self._name = value

    @property
    @abstractmethod
    def slug(self):
        """Retuns the slug of the task."""
        pass

    @slug.setter
    def slug(self, value):
        self._slug = value

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

    @fail_text.setter
    def fail_text(self, value):
        self._fail_text = value

    @fail_summary.setter
    def fail_summary(self, value):
        self._fail_summary = value

    @property
    @abstractmethod
    def pass_summary(self) -> str:
        """Summary to return if task passes."""
        pass

    @pass_summary.setter
    def pass_summary(self, value):
        self._pass_summary = value

    @property
    @abstractmethod
    def pass_text(self) -> str:
        """Longer description to return if task passes."""
        pass

    @pass_text.setter
    def pass_text(self, value):
        self._pass_text = value

    @property
    @abstractmethod
    def actions(self) -> dict:
        """If task allows actions to be taken, return here."""
        pass

    def execute(self, github_body, settings, fail_text, settings_content="rubocop_config") -> str:
        """Logic to execute for task"""
        head_branch = github_body["pull_request"]["head"]["ref"]
        base_branch = github_body["repository"]["default_branch"]
        result = self.code_check_execute(github_body, head_branch, base_branch, settings, settings_content)
        return result

    def code_check_execute(self, github_body, head_branch, base_branch, settings, settings_content):
        code_check = CodeCheck(
            token=github_body.get("githaxs").get("token"),
            branch=head_branch,
            default_branch=base_branch,
            full_repo_name=github_body.get("repository", {}).get("full_name"),
            source_script_path="%s/task.sh" % os.path.dirname(__file__),
            setting_files=[
                {
                    "file_name": ".rubocop.yaml",
                    "contents": dump(settings[settings_content]),
                }
            ],
        )
        code_check.execute()
        self.fail_text = code_check.fail_text
        return code_check.result

    @property
    @abstractmethod
    def subscription_level(self) -> str:
        """Subscription level app is available on"""
        pass

    @subscription_level.setter
    def subscription_level(self, value):
        self._subscription_level = value
