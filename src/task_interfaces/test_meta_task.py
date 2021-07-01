import os
from typing import Dict

from code_check import CodeCheck
from meta_task import MetaTaskInterface
from subscription_levels import SubscriptionLevels
from yaml import dump


class Task(MetaTaskInterface):
    """
    a linter for ruby and rails repo
    """

    name = "rubocop"
    slug = "rubocop "
    pass_summary = ""
    pass_text = ""
    fail_summary = ""
    fail_text = ""
    subscription_level = SubscriptionLevels.FREE

    actions = None

    def __init__(self, *args, **kwargs):
        task_variables = [self.name, self.slug, self.pass_summary, self.pass_text, self.fail_text, self.fail_summary,
                          self.subscription_level]
        super().__init__(*task_variables, *kwargs)

    def execute(self, github_body, settings, *args, **kwargs) -> bool:
        result = super(Task, self).execute(github_body, settings, *args, **kwargs)
        return result


if __name__ == "__main__":
    task = Task()
    github_body = {
        "pull_request": {
            "head": {
                "ref": 1
            }
        },
        "repository": {
            "default_branch": 'master'
        }
    }
    settings = {
        "rubocop_config": {
            "task": 'rubocop'
        }
    }

task.execute(github_body, settings, '')
