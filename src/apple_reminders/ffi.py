import ctypes
import sys
from pathlib import Path

if sys.platform != "darwin":
    raise RuntimeError("This package only supports macOS")

def find_library() -> Path:
    """Find the RemindersLib dylib."""
    # First, check if we're in development mode (editable install)
    script_dir = Path(__file__).parent.parent.parent
    dev_lib = script_dir / ".build/release/libRemindersLib.dylib"
    if dev_lib.exists():
        return dev_lib
        
    # Otherwise, look in the package's lib directory
    package_lib = Path(__file__).parent / "lib/libRemindersLib.dylib"
    if package_lib.exists():
        return package_lib
        
    raise RuntimeError(
        "Swift library not found. This could mean:\n"
        "1. You're in development and haven't built the library ('swift build -c release')\n"
        "2. The package was not installed correctly\n"
        "3. You're not on macOS"
    )

# Load the dynamic library
_lib = ctypes.CDLL(str(find_library()))

# Define the function signatures
_lib.CreateRemindersReader.restype = ctypes.c_void_p
_lib.CreateRemindersReader.argtypes = []

_lib.DestroyRemindersReader.restype = None
_lib.DestroyRemindersReader.argtypes = [ctypes.c_void_p]

_lib.GetReminders.restype = ctypes.POINTER(ctypes.c_char)
_lib.GetReminders.argtypes = [ctypes.c_void_p]

_lib.GetReminderLists.restype = ctypes.POINTER(ctypes.c_char)
_lib.GetReminderLists.argtypes = [ctypes.c_void_p]

_lib.GetRemindersInList.restype = ctypes.POINTER(ctypes.c_char)
_lib.GetRemindersInList.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.SearchReminders.restype = ctypes.POINTER(ctypes.c_char)
_lib.SearchReminders.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.CreateReminder.restype = ctypes.POINTER(ctypes.c_char)
_lib.CreateReminder.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.CreateList.restype = ctypes.POINTER(ctypes.c_char)
_lib.CreateList.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.CompleteReminder.restype = ctypes.POINTER(ctypes.c_char)
_lib.CompleteReminder.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.UncompleteReminder.restype = ctypes.POINTER(ctypes.c_char)
_lib.UncompleteReminder.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.FreeString.restype = None
_lib.FreeString.argtypes = [ctypes.POINTER(ctypes.c_char)]