import json, sys
j = json.load(open('params.json'))
dflt = bytes.fromhex(j['program_layout']['default_program_bytes_hex'])
lim = {e['nrpn_or_byte_index']: e['max'] for e in j['value_limits_on_receive']['entries']}
glim = {e['nrpn']: e for e in j['globals_limits_on_receive']['entries']}
def unpack7(p, n):
    out = bytearray()
    for g in range(0, len(p), 8):
        for k in range(7):
            if len(out) < n: out.append(((p[g] >> k) & 1) << 7 | p[g + 1 + k])
    return bytes(out)
eb = open('work/dumps/editbuffer_04.syx', 'rb').read()
print('header', eb[:8].hex(' '), 'version', eb[7], 'fin', hex(eb[-1]))
prog = unpack7(eb[8:-1], 242)
print('nom:', prog[223:239])
for i in range(0, 242, 16): print(f'{i:3d}:', ' '.join(f'{x:02x}' for x in prog[i:i+16]))
print('hors bornes:', [(i, prog[i], lim[i]) for i in lim if prog[i] > lim[i]])
print('diff vs defaut:', sum(1 for a, b in zip(prog, dflt) if a != b), 'octets')
open('work/dumps/editbuffer_prog242.bin', 'wb').write(prog)
g = open('work/dumps/globals_06.syx', 'rb').read()
print('globals header', g[:8].hex(' '), 'len', len(g))
gp = unpack7(g[8:-1], 55)
print('globals:', ' '.join(f'{x:02x}' for x in gp))
print('hors bornes globals:', [(300 + i, gp[i], glim[300 + i]['max']) for i in range(55) if gp[i] > glim[300 + i]['max']])
open('work/dumps/globals_55.bin', 'wb').write(gp)
