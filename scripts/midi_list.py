import ctypes
from ctypes import wintypes
winmm = ctypes.WinDLL('winmm')
class MIDIINCAPS(ctypes.Structure):
    _fields_ = [('wMid', wintypes.WORD), ('wPid', wintypes.WORD), ('vDriverVersion', wintypes.UINT), ('szPname', ctypes.c_wchar * 32), ('dwSupport', wintypes.DWORD)]
class MIDIOUTCAPS(ctypes.Structure):
    _fields_ = [('wMid', wintypes.WORD), ('wPid', wintypes.WORD), ('vDriverVersion', wintypes.UINT), ('szPname', ctypes.c_wchar * 32), ('wTechnology', wintypes.WORD), ('wVoices', wintypes.WORD), ('wNotes', wintypes.WORD), ('wChannelMask', wintypes.WORD), ('dwSupport', wintypes.DWORD)]
for i in range(winmm.midiInGetNumDevs()):
    c = MIDIINCAPS(); winmm.midiInGetDevCapsW(i, ctypes.byref(c), ctypes.sizeof(c)); print('IN ', i, c.szPname)
for i in range(winmm.midiOutGetNumDevs()):
    c = MIDIOUTCAPS(); winmm.midiOutGetDevCapsW(i, ctypes.byref(c), ctypes.sizeof(c)); print('OUT', i, c.szPname)
