import sys, collections
sys.path.insert(0, 'scripts')
import midi_safe as m

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 10
label = sys.argv[2] if len(sys.argv) > 2 else ''
d = m.Midi(0, None)
msgs = d.take(secs)
d.close()
m.log('--- fin ecoute: ' + label)
nrpn = {}
cur = {'msb': None, 'lsb': None, 'dm': 0}
events = []
ccs = collections.Counter()
for x in msgs:
    st = x[0]
    if st >= 0xF0 and st != 0xF0:
        continue
    if st == 0xF0:
        events.append(('SYSEX', len(x), x[:10].hex(' ')))
        continue
    t = st & 0xF0
    if t in (0x80, 0x90):
        continue
    if t == 0xB0:
        c, v = x[1], x[2]
        if c == 99: cur['msb'] = v
        elif c == 98: cur['lsb'] = v
        elif c == 6: cur['dm'] = v
        elif c == 38:
            if cur['msb'] is not None and cur['lsb'] is not None:
                n = cur['msb'] * 128 + cur['lsb']
                events.append(('NRPN', n, cur['dm'] * 128 + v))
        else:
            ccs[c] += 1
            events.append(('CC', c, v))
    else:
        events.append(('OTHER', x.hex(' ')))
print('etiquette:', label, '| messages non-note:', len(events))
seq = collections.OrderedDict()
for e in events:
    seq.setdefault(e[:2], []).append(e[2] if len(e) > 2 else None)
for k, vals in seq.items():
    vv = [v for v in vals if isinstance(v, int)]
    print(k, 'n=%d' % len(vals), 'min/max=' + str((min(vv), max(vv)) if vv else None), 'exemples', vals[:12])
