import sys
sys.path.insert(0, 'scripts')
import midi_safe as m

d = m.Midi(0, 1)
d.take(0.5)
d.send_sysex(bytes([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7]))
for r in d.take(2.0):
    if r[0] == 0xF0:
        print('SYSEX', len(r), 'octets :', r.hex(' '))
d.close()
