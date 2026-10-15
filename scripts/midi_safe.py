import ctypes, os, time, threading
from ctypes import wintypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
winmm = ctypes.WinDLL('winmm')
READ_CMDS = {0x01: 2, 0x03: 0, 0x0A: 1, 0x73: 0}
os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
LOG = open(os.path.join(ROOT, 'work', 'midi_log.txt'), 'a', buffering=1)


def log(s):
    LOG.write(time.strftime('%H:%M:%S ') + s + '\n')


def check_tx(b):
    b = bytes(b)
    if len(b) < 6 or b[0] != 0xF0 or b[-1] != 0xF7 or any(x >= 0x80 for x in b[1:-1]):
        raise ValueError('pas une trame sysex valide')
    if len(b) == 6 and b[1] == 0x7E and b[3:5] == b'\x06\x01':
        return
    if len(b) >= 8 and b[1:5] == b'\x00\x20\x32\x20' and b[6] in READ_CMDS and len(b) == 8 + READ_CMDS[b[6]]:
        return
    raise ValueError('trame REFUSEE par la liste blanche: ' + b.hex(' '))


class Hdr(ctypes.Structure):
    _fields_ = [('lpData', ctypes.c_void_p), ('dwBufferLength', wintypes.DWORD), ('dwBytesRecorded', wintypes.DWORD),
                ('dwUser', ctypes.c_size_t), ('dwFlags', wintypes.DWORD), ('lpNext', ctypes.c_void_p),
                ('reserved', ctypes.c_size_t), ('dwOffset', wintypes.DWORD), ('dwReserved', ctypes.c_size_t * 4)]


CB = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, wintypes.UINT, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t)


class Midi:
    def __init__(self, in_dev, out_dev):
        self.rx = []
        self.lock = threading.Lock()
        self.hin = ctypes.c_void_p()
        self.hout = ctypes.c_void_p()
        self.cb = CB(self._cb)
        r = winmm.midiInOpen(ctypes.byref(self.hin), in_dev, self.cb, 0, 0x30000)
        assert r == 0, 'midiInOpen %d' % r
        self.bufs = []
        for _ in range(4):
            buf = ctypes.create_string_buffer(8192)
            h = Hdr()
            h.lpData = ctypes.cast(buf, ctypes.c_void_p)
            h.dwBufferLength = 8192
            winmm.midiInPrepareHeader(self.hin, ctypes.byref(h), ctypes.sizeof(h))
            winmm.midiInAddBuffer(self.hin, ctypes.byref(h), ctypes.sizeof(h))
            self.bufs.append((buf, h))
        winmm.midiInStart(self.hin)
        if out_dev is not None:
            r = winmm.midiOutOpen(ctypes.byref(self.hout), out_dev, 0, 0, 0)
            assert r == 0, 'midiOutOpen %d' % r

    def _cb(self, hnd, msg, inst, p1, p2):
        if msg == 0x3C3:
            st = p1 & 0xFF
            d = [st, (p1 >> 8) & 0xFF, (p1 >> 16) & 0xFF]
            n = 1 if st >= 0xF8 else (2 if (st & 0xF0) in (0xC0, 0xD0) else 3)
            m = bytes(d[:n])
            if st != 0xFE:
                log('RX ' + m.hex(' '))
                with self.lock:
                    self.rx.append(m)
        elif msg == 0x3C4:
            for buf, h in self.bufs:
                if ctypes.addressof(h) == p1:
                    m = bytes(buf.raw[:h.dwBytesRecorded])
                    if m:
                        log('RX SYSEX %d o: ' % len(m) + m.hex(' '))
                        with self.lock:
                            self.rx.append(m)
                        winmm.midiInAddBuffer(self.hin, ctypes.byref(h), ctypes.sizeof(h))

    def send_sysex(self, b):
        check_tx(b)
        b = bytes(b)
        log('TX ' + b.hex(' '))
        buf = ctypes.create_string_buffer(b, len(b))
        h = Hdr()
        h.lpData = ctypes.cast(buf, ctypes.c_void_p)
        h.dwBufferLength = len(b)
        winmm.midiOutPrepareHeader(self.hout, ctypes.byref(h), ctypes.sizeof(h))
        winmm.midiOutLongMsg(self.hout, ctypes.byref(h), ctypes.sizeof(h))
        time.sleep(0.3)
        winmm.midiOutUnprepareHeader(self.hout, ctypes.byref(h), ctypes.sizeof(h))

    def take(self, wait=1.0):
        time.sleep(wait)
        with self.lock:
            r, self.rx = self.rx, []
        return r

    def close(self):
        winmm.midiInStop(self.hin)
        winmm.midiInReset(self.hin)
        winmm.midiInClose(self.hin)
        if self.hout:
            winmm.midiOutClose(self.hout)
