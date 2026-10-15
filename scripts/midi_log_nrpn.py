import sys, collections
lines = open('work/midi_log.txt').read().split('\n')
idx = [i for i, l in enumerate(lines) if '--- fin ecoute' in l]
skip = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = idx[-1 - skip] if idx else len(lines)
start = idx[-2 - skip] if len(idx) > 1 + skip else 0
cur = {}
out = collections.OrderedDict()
for l in lines[start:end]:
    if ' RX ' not in l or 'SYSEX' in l: continue
    b = [int(x, 16) for x in l.split('RX ')[1].split()]
    if (b[0] & 0xF0) != 0xB0: continue
    c, v = b[1], b[2]
    if c == 99: cur['msb'] = v
    elif c == 98: cur['lsb'] = v
    elif c == 6: cur['dm'] = v
    elif c == 38:
        n = cur.get('msb', 0) * 128 + cur.get('lsb', 0)
        out.setdefault(n, []).append(cur.get('dm', 0) * 128 + v)
    else:
        out.setdefault('CC%d' % c, []).append(v)
for n, vals in out.items():
    print('NRPN' if isinstance(n, int) else '', n, 'n=%d' % len(vals), 'min/max=(%d,%d)' % (min(vals), max(vals)), vals[:10], '...')
