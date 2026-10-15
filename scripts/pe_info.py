import struct, sys, datetime
d = open(sys.argv[1], 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]
assert d[pe:pe+4] == b'PE\0\0'
mach, nsec, ts, _, _, optsz, chars = struct.unpack_from('<HHIIIHH', d, pe+4)
opt = pe + 24
magic = struct.unpack_from('<H', d, opt)[0]
is64 = magic == 0x20b
print('machine', hex(mach), 'PE32+' if is64 else 'PE32', 'timestamp', datetime.datetime.utcfromtimestamp(ts), 'chars', hex(chars))
maj, mnr = struct.unpack_from('<BB', d, opt+2)
print('linker version', maj, mnr)
ep, = struct.unpack_from('<I', d, opt+16)
base, = struct.unpack_from('<Q' if is64 else '<I', d, opt+24 if is64 else opt+28)
print('entrypoint RVA', hex(ep), 'imagebase', hex(base))
ddoff = opt + (112 if is64 else 96)
names = ['export','import','resource','exception','security','reloc','debug','arch','gp','tls','loadcfg','boundimp','iat','delayimp','clr','res']
dd = [struct.unpack_from('<II', d, ddoff+8*i) for i in range(16)]
for n, (r, s) in zip(names, dd):
    if r or s: print(' dir', n, hex(r), hex(s))
secs = []
so = opt + optsz
for i in range(nsec):
    nm, vs, va, rs, rp = struct.unpack_from('<8sIIII', d, so+40*i)
    fl, = struct.unpack_from('<I', d, so+40*i+36)
    secs.append((nm.rstrip(b'\0').decode(), vs, va, rs, rp, fl))
    import math
    data = d[rp:rp+rs]
    ent = 0
    if data:
        from collections import Counter
        c = Counter(data); n = len(data)
        ent = -sum(v/n*math.log2(v/n) for v in c.values())
    print(f' sec {secs[-1][0]:8} vsize={vs:#x} va={va:#x} rsize={rs:#x} raw={rp:#x} flags={fl:#x} entropy={ent:.2f}')
def rva2off(r):
    for nm, vs, va, rs, rp, fl in secs:
        if va <= r < va+max(vs, rs): return r - va + rp
r, s = dd[1]
if r:
    o = rva2off(r); dlls = []
    while True:
        oft, _, _, nm, ft = struct.unpack_from('<IIIII', d, o)
        if not nm: break
        p = rva2off(nm); dlls.append(d[p:d.index(b'\0', p)].decode())
        o += 20
    print('imports:', dlls)
