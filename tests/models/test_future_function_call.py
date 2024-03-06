from asyncio import get_event_loop
from dataclasses import FrozenInstanceError
from unq.models import _FutureFunctionCall
import pytest

@pytest.fixture
def default_ffc():
    # Arrange
    future = get_event_loop().create_future()
    function = print
    args = ("Hello, World!",)
    kwargs = {"test": "arg"}
    return _FutureFunctionCall(future=future, function=function, args=args, kwargs=kwargs)


def test_constructor_properly_creates_object():
    # Arrange
    future = get_event_loop().create_future()
    function = print
    args = ("Hello, World!",)
    kwargs = {"test": "arg"}
    
    # Act
    ffc = _FutureFunctionCall(future=future, function=function, args=args, kwargs=kwargs)
    
    # Assert
    assert ffc.future == future, "Future did not match"
    assert ffc.function == function, "Function did not match"
    assert ffc.args == args, "Args did not match"
    assert ffc.kwargs == kwargs, "Kwargs did not match"
    
    
def test_object_is_immutable(default_ffc):
    # Arrange
    assign_to_ffc = lambda: setattr(default_ffc, "kwargs", {"test": "arg2"})
    
    # Act, Assert
    assert pytest.raises(FrozenInstanceError, assign_to_ffc)