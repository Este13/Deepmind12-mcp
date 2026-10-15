import json, csv, collections
j = json.load(open('params.json'))
prog = bytes.fromhex(j['program_layout']['default_program_bytes_hex'])
lim = {e['nrpn_or_byte_index']: e['max'] for e in j['value_limits_on_receive']['entries']}
sec = {}
for k, v in j['sections_nrpn'].items():
    if isinstance(v, list):
        for n in v: sec.setdefault(n, []).append(k.split(' (')[0])
nm = {}
for e in j['named_controls_observed_on_hardware']['entries']:
    for tok in str(e['nrpn']).replace(' et ', ';').split(';'):
        if tok.strip().isdigit(): nm[int(tok)] = (e['section'] + ' ' + e['controle']).strip()
kinds = collections.defaultdict(set)
for b in j['ui_bindings']['entries']:
    if b['nrpn'] is not None: kinds[b['nrpn']].add(b['kind'])
def region(i):
    if i == 0x55: return 'special (FUN_140404b70)'
    if 223 <= i <= 238: return 'name'
    if 166 <= i <= 217: return 'fx slot %d %s' % ((i - 166) // 13 + 1, 'type' if (i - 166) % 13 == 0 else 'param %d' % ((i - 166) % 13 - 1))
    if 218 <= i <= 221: return 'fx %d level?' % (i - 217)
    if 93 <= i <= 116: return 'modmatrix slot %d %s' % ((i - 93) // 3 + 1, ['source', 'destination', 'depth?'][(i - 93) % 3])
    return ''
with open('notes/patch_map.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['byte_index(=NRPN)', 'default', 'max_on_receive(prouve)', 'region(infere sauf mention)', 'sections_ui(bindings)', 'binding_kinds', 'nom_observe_sur_materiel'])
    for i in range(242):
        w.writerow([i, prog[i], lim.get(i, ''), region(i), '/'.join(sec.get(i, [])), ','.join(sorted(kinds.get(i, []))), nm.get(i, '')])
print('ok')
