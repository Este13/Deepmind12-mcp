import sys, os, time, json
sys.path.insert(0, 'scripts')
import midi_safe as ms
import midi_dm12 as dm

HOLD = 30
P = dm._P
default = bytearray(bytes.fromhex(P['program_layout']['default_program_bytes_hex']))
labels = P['label_tables']['pointer_table_0x14086e9b0']['labels'][:133]
dest_vcf_freq = labels.index('VCF Freq')

t = bytearray(default)
t[39] = 150
t[41] = 40
t[42] = 90
t[53], t[54], t[55], t[56] = 12, 90, 150, 70
t[0] = 60
t[93], t[94], t[95] = 6, dest_vcf_freq, 0x90
t[166] = 27
for k, p in enumerate(dm.EFFECTS[27]['params']):
    t[167 + k] = p['default_step'] if p['default_step'] <= abs(p['steps']) - 1 else abs(p['steps']) - 1
t[167 + 5] = 20
t[223:239] = b'MCP TEST        '
T = bytes(t)

errs = dm.validate_program(T)
print('validation du patch de test :', errs or 'OK')
if errs:
    sys.exit(1)

os.makedirs('work/dumps', exist_ok=True)
d = ms.Midi(0, 1)
try:
    e0 = dm.read_edit_buffer(d)
    open('work/dumps/backup_before_full_%s.syx' % time.strftime('%H%M%S'), 'wb').write(e0)
    p0 = dm.parse_edit_buffer(e0)
    print('etat initial : %r' % bytes(p0[223:239]).decode())
    dm.write_edit_buffer(d, T, confirm=dm.CONFIRM)
    e1 = dm.read_edit_buffer(d)
    p1 = dm.parse_edit_buffer(e1)
    diff = [(i, T[i], p1[i]) for i in range(242) if T[i] != p1[i]]
    print('relecture identique au patch envoye :', not diff)
    if diff:
        print('octets modifies par le firmware (index, envoye, relu) :', diff)
    print('nom relu : %r' % bytes(p1[223:239]).decode())
    print('patch de test ACTIF pendant %d s (baisse le volume avant de jouer)...' % HOLD)
    time.sleep(HOLD)
finally:
    try:
        dm.write_edit_buffer(d, p0, confirm=dm.CONFIRM)
        e3 = dm.read_edit_buffer(d)
        print('restauration -> identique a l\'etat initial :', e3 == e0)
    except Exception as ex:
        print('!! restauration impossible :', ex)
    d.close()
