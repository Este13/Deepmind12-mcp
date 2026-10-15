import json, os, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_safe as ms

HDR = bytes([0xF0, 0x00, 0x20, 0x32, 0x20])
PROG_LEN = 242
_P = json.load(open(os.path.join(ms.ROOT, 'params.json'), encoding='utf-8'))
LIMITS = {e['nrpn_or_byte_index']: e['max'] for e in _P['value_limits_on_receive']['entries']}
EFFECTS = {e['id']: e for e in _P['effects']['list']}


def pack7(data):
    out = bytearray()
    for g in range(0, len(data), 7):
        chunk = data[g:g + 7]
        msb = 0
        for j, b in enumerate(chunk):
            msb |= (b >> 7) << j
        out.append(msb)
        out.extend(b & 0x7F for b in chunk)
        out.extend([0] * (7 - len(chunk)))
    return bytes(out)


def unpack7(p, n):
    out = bytearray()
    for g in range(0, len(p), 8):
        for j in range(7):
            if len(out) < n:
                out.append(((p[g] >> j) & 1) << 7 | p[g + 1 + j])
    return bytes(out)


def build_edit_buffer(prog, dev=0):
    assert len(prog) == PROG_LEN and 0 <= dev < 0x80
    return HDR + bytes([dev, 0x04, 0x07]) + pack7(prog) + b'\xF7'


def parse_edit_buffer(msg):
    if len(msg) != 289 or msg[:5] != HDR or msg[6] != 4 or msg[7] != 7 or msg[-1] != 0xF7:
        raise ValueError('edit buffer inattendu: len=%d head=%s' % (len(msg), msg[:8].hex(' ')))
    return unpack7(msg[8:-1], PROG_LEN)


def validate_program(prog):
    err = []
    if len(prog) != PROG_LEN:
        return ['longueur %d != 242' % len(prog)]
    for i, mx in LIMITS.items():
        if prog[i] > mx:
            err.append('octet %d = %d > max %d (borne de l\'editeur)' % (i, prog[i], mx))
    for s in range(4):
        t = prog[166 + 13 * s]
        if t > 35:
            err.append('slot %d: type d\'effet %d > 35' % (s + 1, t)); continue
        for k, p in enumerate(EFFECTS[t]['params']):
            v = prog[167 + 13 * s + k]
            if v > abs(p['steps']) - 1:
                err.append('slot %d %s.%s = %d > %d' % (s + 1, EFFECTS[t]['name'], p['name'], v, abs(p['steps']) - 1))
    for i in range(4):
        if prog[218 + i] > 150:
            err.append('niveau FX %d = %d > 150' % (i + 1, prog[218 + i]))
    name = prog[223:239]
    if any(c < 0x20 or c > 0x7E for c in name):
        err.append('nom: caracteres non ASCII imprimables %r' % bytes(name))
    return err


def read_edit_buffer(d, dev=0, wait=2.0):
    d.take(0.3)
    d.send_sysex(HDR + bytes([dev, 0x03, 0xF7]))
    for r in d.take(wait):
        if len(r) == 289 and r[6] == 4:
            return r
    raise RuntimeError('pas de reponse EditBufferDump')


CONFIRM = 'EDIT_BUFFER_ONLY'


def write_edit_buffer(d, prog, dev=0, confirm=None):
    if confirm != CONFIRM:
        raise PermissionError('confirmation manquante')
    errs = validate_program(prog)
    if errs:
        raise ValueError('programme refuse: ' + '; '.join(errs))
    msg = build_edit_buffer(prog, dev)
    _send_edit_buffer_raw(d, msg)
    return msg


def _send_edit_buffer_raw(d, b):
    b = bytes(b)
    ok = (len(b) == 289 and b[:5] == HDR and b[5] < 0x80 and b[6] == 0x04 and b[7] == 0x07
          and b[-1] == 0xF7 and all(x < 0x80 for x in b[1:-1]))
    if not ok:
        raise ValueError("trame d'ecriture REFUSEE (pas un edit buffer valide)")
    ms.log('TX EDITBUFFER 289 o: ' + b.hex(' '))
    buf = ms.ctypes.create_string_buffer(b, len(b))
    h = ms.Hdr()
    h.lpData = ms.ctypes.cast(buf, ms.ctypes.c_void_p)
    h.dwBufferLength = len(b)
    ms.winmm.midiOutPrepareHeader(d.hout, ms.ctypes.byref(h), ms.ctypes.sizeof(h))
    ms.winmm.midiOutLongMsg(d.hout, ms.ctypes.byref(h), ms.ctypes.sizeof(h))
    time.sleep(0.5)
    ms.winmm.midiOutUnprepareHeader(d.hout, ms.ctypes.byref(h), ms.ctypes.sizeof(h))
