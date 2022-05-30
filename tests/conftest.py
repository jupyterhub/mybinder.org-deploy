import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--binder-url",
        help="Fully qualified URL to the binder installation"
    )

    parser.addoption(
        "--hub-url",
        help="Fully qualified URL to the hub installation"
    )


@pytest.fixture
def binder_url(request):
    return request.config.getoption("--binder-url").rstrip("/")


@pytest.fixture
def hub_url(request):
    return request.config.getoption("--hub-url").rstrip("/")
