from src.task_interfaces import Task


def test_capabilities():
    task = Task(
        name="Test",
        slug="test",
        summary="",
        description="",
        capabilities=[{'type': 'checkout'}],
        subscription_level=2,
        runtime='python',
    )

    assert 0 == 0


def test_get_subscribed_events():
    task = Task(
        name="Test",
        slug="test",
        summary="",
        description="",
        capabilities=[{'type': 'checkrun'}],
        subscription_level=2,
        runtime='python',
    )

    assert task.has_check_run_capability() is True


def test_get_actions():
    task = Task(name="Test",
                slug="test",
                summary="",
                description="",
                capabilities=[{'type': 'checkrun',
                               'actions': [{'label': 'fix',
                                            'identifier': 'fix',
                                            'description': 'fix'}]},
                              {'type': 'checkout',
                               'depth': 5},
                              {'type': 'aws-assume-iam-role'}],
                subscription_level=2,
                runtime='python',
                )

    assert len(task.get_check_run_actions()) == 1


def test_iam_role_paremeters():
    task = Task(
        name="Test",
        slug="test",
        summary="",
        description="",
        capabilities=[
            {
                'type': 'aws-assume-iam-role',
            },
        ],
        subscription_level=2,
        runtime='python',
    )

    parameters = task.get_parameters()

    assert parameters[0]['name'] == 'iam_role_arn'


def test_slug():
    task = Task(
        name="Test Foo Bar",
        summary="",
        description="",
        capabilities=[
            {
                'type': 'aws-assume-iam-role',
            },
        ],
        subscription_level=2,
        runtime='python',
    )

    assert 'slug' in task.dict()
    assert task.dict()['slug'] == 'test-foo-bar'
