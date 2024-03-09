from asyncio import new_event_loop
from dataclasses import FrozenInstanceError

import pytest

from unq.models import _FutureFunctionCall


@pytest.fixture
def default_future():
    return new_event_loop().create_future()


@pytest.fixture
def default_ffc(default_future):
    # Arrange
    future = default_future
    function = print
    args = ("Hello, World!",)
    kwargs = {"test": "arg"}
    return _FutureFunctionCall(
        future=future, function=function, args=args, kwargs=kwargs
    )


def test_constructor_properly_creates_object(default_ffc, default_future):
    # Arrange
    future = default_future
    function = print
    args = ("Hello, World!",)
    kwargs = {"test": "arg"}

    # Assert
    assert default_ffc.future == future, "Future did not match"
    assert default_ffc.function == function, "Function did not match"
    assert default_ffc.args == args, "Args did not match"
    assert default_ffc.kwargs == kwargs, "Kwargs did not match"


def test_object_is_immutable_dataclass(default_ffc):
    # Act, Assert
    with pytest.raises(FrozenInstanceError):
        default_ffc.kwargs = {"arg": "value"}
