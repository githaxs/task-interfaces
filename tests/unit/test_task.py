import pytest
from src.task_interfaces.task import SubscriptionLevels
from src.task_interfaces.task import TaskInterface
from src.task_interfaces.task import TaskTypes


class Foo(TaskInterface):
    name = "foo"
    slug = "foo"
    fail_summary = ""
    fail_text = ""
    pass_summary = ""
    pass_text = ""
    actions = ""
    subscription_level = SubscriptionLevels.FREE
    type = TaskTypes.CODE_ANALYSIS
    type = ""
    command = "prettier"

    def execute(self, github_body):
        pass


def test_throws_with_invalid_subscription_level():
    with pytest.raises(Exception) as e_info:
        Foo.subscription_level = "bar"
        foo = Foo()
        print(e_info)


def test_throws_with_invalid_type():
    with pytest.raises(Exception) as e_info:
        Foo.type = "bar"
        foo = Foo()
        print(e_info)

    Foo.type = TaskTypes.CODE_ANALYSIS
    Foo.subscription_level = SubscriptionLevels.FREE
    foo = Foo()


def test_source_handler():
    with pytest.raises(Exception) as e_info:
        Foo.command = None
        Foo.handler = "bar"
        foo = Foo()
        print(e_info)

    with pytest.raises(Exception) as e_info:
        Foo.command = None
        Foo.source_script = "bar"
        Foo.handler = None
        foo = Foo()
        print(e_info)

    Foo.source_script = "bar"
    Foo.handler = "bar"
    foo = Foo()


def test_bad_slug():
    Foo.slug = "0000"

    with pytest.raises(Exception) as e_info:
        foo = Foo()
        print(e_info)

    Foo.slug = "bar"
    foo = Foo()
