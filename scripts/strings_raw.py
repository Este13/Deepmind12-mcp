import re, struct, sys

d = open(sys.argv[1], 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]
nsec, = struct.unpack_from('<H', d, pe + 6)
optsz, = struct.unpack_from('<H', d, pe + 20)
base, = struct.unpack_from('<Q', d, pe + 24 + 24)
secs = []
for i in range(nsec):
    nm, vs, va_, rs, rp = struct.unpack_from('<8sIIII', d, pe + 24 + optsz + 40 * i)
    secs.append((nm.rstrip(b'\0').decode(), va_, rp, rs))


def va(off):
    for nm, v, rp, rs in secs:
        if rp <= off < rp + rs:
            return base + v + off - rp, nm
    return None, '?'


def esc(t):
    return t.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def fa(a):
    return '-' if a is None else hex(a)


out = open(sys.argv[2], 'w', encoding='utf-8')
n = 0
for m in re.finditer(rb'[\x20-\x7e\t\r\n]{4,}', d):
    a, s = va(m.start())
    out.write(fa(a) + '\t' + s + '\tA\t' + esc(m.group().decode()) + '\n')
    n += 1
for m in re.finditer(rb'(?:[\x20-\x7e]\x00){4,}', d):
    a, s = va(m.start())
    out.write(fa(a) + '\t' + s + '\tW\t' + esc(m.group().decode('utf-16le')) + '\n')
    n += 1
print(n)
