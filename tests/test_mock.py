"""Test that MockSwiftAPI correctly implements all required function signatures."""

import ctypes
import inspect
from typing import Any, Dict

import pytest

from apple_reminders.ffi import _lib
from apple_reminders.mock import MockSwiftAPI


def get_required_signatures() -> Dict[str, Dict[str, Any]]:
    """Return the required function signatures from the original library using reflection."""
    signatures = {}

    # Get all attributes that look like functions (have restype and argtypes)
    for name, value in inspect.getmembers(_lib):
        # Skip internal/private attributes
        if name.startswith("_"):
            continue

        # Check if it has the characteristics of a ctypes function
        if hasattr(value, "restype") and hasattr(value, "argtypes"):
            signatures[name] = {
                "restype": value.restype,
                "argtypes": value.argtypes if value.argtypes is not None else [],
            }

    return signatures


def test_required_functions_exist() -> None:
    """Test that all required functions exist in MockSwiftAPI."""
    mock_api = MockSwiftAPI()
    required_signatures = get_required_signatures()

    missing_functions = []
    for func_name in required_signatures:
        if not hasattr(mock_api, func_name):
            missing_functions.append(func_name)

    if missing_functions:
        pytest.fail(
            "MockSwiftAPI is missing these required functions:\n"
            + "\n".join(f"- {func}: {required_signatures[func]}" for func in missing_functions)
        )


def test_function_signatures() -> None:
    """Test that function signatures match the required ones."""
    mock_api = MockSwiftAPI()
    required_signatures = get_required_signatures()

    signature_mismatches = []
    implemented_functions = [func for func in required_signatures if hasattr(mock_api, func)]

    for func_name in implemented_functions:
        mock_func = getattr(mock_api, func_name)
        required_sig = required_signatures[func_name]

        # For implemented functions, verify they accept the correct arguments
        mock_args = mock_func.__code__.co_varnames[: mock_func.__code__.co_argcount]
        required_args_count = len(required_sig["argtypes"])

        # First arg is self, so we need to adjust the comparison
        if len(mock_args) - 1 != required_args_count:
            signature_mismatches.append(
                f"{func_name}:\n"
                + f"  Expected {required_args_count} arguments: {required_sig['argtypes']}\n"
                + f"  Got {len(mock_args) - 1} arguments: {mock_args[1:]}"
            )

    if signature_mismatches:
        pytest.fail("Function signature mismatches found:\n" + "\n".join(signature_mismatches))


def test_return_values_match_expected() -> None:
    """Test that return value types match the expected types by checking method annotations."""
    mock_api = MockSwiftAPI()
    required_signatures = get_required_signatures()

    return_type_mismatches = []

    # Get all implemented methods that should have return type annotations
    implemented_methods = {
        name: getattr(mock_api.__class__, name)
        for name in required_signatures
        if hasattr(mock_api.__class__, name)
    }

    for method_name, method in implemented_methods.items():
        if not hasattr(method, "__annotations__"):
            return_type_mismatches.append(f"{method_name}: No return type annotation found")
            continue

        # Get the expected return type from the original library
        expected_type = required_signatures[method_name]["restype"]
        # Get the actual return type from the method annotation
        actual_type = method.__annotations__.get("return")

        # Convert string annotation back to type if needed
        if isinstance(actual_type, str):
            if "ctypes.POINTER(ctypes.c_char)" in actual_type:
                actual_type = ctypes.POINTER(ctypes.c_char)

        if actual_type != expected_type:
            return_type_mismatches.append(
                f"{method_name}:\n"
                + f"  Expected return type: {expected_type}\n"
                + f"  Got return type: {actual_type}"
            )

    if return_type_mismatches:
        pytest.fail("Return type mismatches found:\n" + "\n".join(return_type_mismatches))
