import struct, sys, json
d = open(sys.argv[1], 'rb').read()
RD_VA, RD_OFF, RD_SZ = 0x1404d7000, 0x4d5800, 0x17e9a00
def off(va): return va - RD_VA + RD_OFF
def cstr(va, mx=48):
    if not (RD_VA <= va < RD_VA + RD_SZ): return None
    o = off(va); e = d.find(b'\0', o, o + mx + 1)
    if e <= o: return None
    t = d[o:e]
    return t.decode('latin1') if all(32 <= c < 127 for c in t) else None
out = []
va = 0x14051f000
while va < 0x140527300:
    o = off(va + 0x28)
    name_p, short_p = struct.unpack_from('<QQ', d, o)
    n, s = cstr(name_p), cstr(short_p, 8)
    kind, = struct.unpack_from("<I", d, off(va))
    fmt_p, = struct.unpack_from('<Q', d, off(va) + 0x18)
    fmt = cstr(fmt_p, 12)
    if n and s and len(s) <= 5 and True and (fmt is None or '%' in fmt or fmt == 'None') and struct.unpack_from('<Q', d, off(va) + 0x38 - 0)[0] is not None:
        mn, mx = struct.unpack_from('<ff', d, off(va) + 8)
        steps, = struct.unpack_from('<i', d, off(va) + 0x10)
        a, b = struct.unpack_from('<II', d, off(va) + 0x20)
        out.append(dict(va=hex(va), name=n, short=s.strip(), kind=kind, min=round(mn, 6), max=round(mx, 6), steps=steps, fmt=fmt, a=a, default_step=b))
        va += 0x38
    else:
        va += 8
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(len(out), 'descripteurs')
