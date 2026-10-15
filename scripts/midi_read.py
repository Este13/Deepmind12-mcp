import sys, os
sys.path.insert(0, 'scripts')
import midi_safe as m

HDR = bytes([0xF0, 0x00, 0x20, 0x32, 0x20])


def unpack7(p, n):
    out = bytearray()
    for g in range(0, len(p), 8):
        msb = p[g]
        for j in range(7):
            if len(out) < n:
                out.append(((msb >> j) & 1) << 7 | p[g + 1 + j])
    return bytes(out)


os.makedirs('work/dumps', exist_ok=True)
d = m.Midi(0, 1)
dev = 0
for name, cmd in (('editbuffer', 3), ('globals', 5)):
    d.take(0.3)
    d.send_sysex(HDR + bytes([dev, cmd, 0xF7]))
    got = [r for r in d.take(2.0) if r[0] == 0xF0]
    for r in got:
        print(name, len(r), 'octets, cmd', hex(r[6]) if len(r) > 6 else '?')
        open('work/dumps/%s_%02x.syx' % (name, r[6]), 'wb').write(r)
d.close()
