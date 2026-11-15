"""Keeps Windows from idle sleep while the run waits and runs, the way a video player does, by asking for it with
SetThreadExecutionState for as long as this process lives. No setting is changed; the request ends with the process.
A closed lid, or choosing Sleep, still sleeps.

    python stay_awake.py <hours>        exits after that many hours at most, or when killed
"""
import ctypes
import sys
import time

ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
end = time.time() + float(sys.argv[1]) * 3600
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
try:
    while time.time() < end:
        time.sleep(60)
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
finally:
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
