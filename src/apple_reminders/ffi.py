import ctypes
from pathlib import Path

# Find the library relative to the script location
SCRIPT_DIR = Path(__file__).parent.parent.parent
LIB_PATH = SCRIPT_DIR / ".build/debug/libRemindersLib.dylib"

if not LIB_PATH.exists():
    raise RuntimeError(
        f"Swift library not found at {LIB_PATH}. "
        "Make sure you've built the Swift code with 'swift build'"
    )

# Load the dynamic library
_lib = ctypes.CDLL(str(LIB_PATH))

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
