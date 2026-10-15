import struct, json
d = open('work/DeepMind12.exe', 'rb').read()
off = lambda va: va - 0x1404d7000 + 0x4d5800
def cs(va, mx=40):
    if not (0x1404d7000 <= va < 0x141cc0000): return None
    o = off(va); e = d.find(b'\0', o, o + mx + 1)
    if e <= o: return None
    t = d[o:e]
    return t.decode('latin1') if all(32 <= c < 127 for c in t) else None
names = {}
for l in open('work/effect_ctors.txt'):
    import re
    m = re.match(r'ctor (\w+) class=(\w+) descriptors=(\w+)', l)
    names[int(m.group(3), 16)] = (m.group(2), '0x' + m.group(1))
effects = []
for i in range(36):
    va = 0x140522f20 + 0x28 * i
    sp, np_, flag, _, n, b0, b1, _pad, pl = struct.unpack_from('<QQIIIBBHQ', d, off(va))
    e = dict(id=b0, short=cs(sp), name=cs(np_), class_byte=b1, n_params=n, table_va=hex(va), ctor_class=names.get(va, (None, None))[0], ctor=names.get(va, (None, None))[1], params=[])
    for k in range(n):
        r = pl + 0x38 * k; o = off(r)
        mn, mx, steps = struct.unpack_from('<ffi', d, o)
        fmt_p, a, dflt, name_p, short_p, kind = struct.unpack_from('<QIIQQI', d, o + 0x10)
        e['params'].append(dict(index=k, name=cs(name_p), short=(cs(short_p, 8) or '').strip(), min=round(mn, 6), max=round(mx, 6), steps=steps, value_range=[0, abs(steps) - 1], fmt=cs(fmt_p, 12), a=a, default_step=dflt, kind=kind, va=hex(r)))
    effects.append(e)
json.dump(effects, open('work/effects.json', 'w'), indent=1)
print(sum(len(e['params']) for e in effects), 'params;', 'defaults hors plage:', sum(1 for e in effects for p in e['params'] if p['default_step'] > abs(p['steps']) - 1))
for e in effects[:3] + effects[28:30]: print(e['id'], e['name'], [(p['name'], p['min'], p['max'], p['steps'], p['default_step']) for p in e['params']][:5])
