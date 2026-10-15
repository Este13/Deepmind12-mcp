import sys, os, time
sys.path.insert(0, 'scripts')
import midi_safe as ms
import midi_dm12 as dm

os.makedirs('work/dumps', exist_ok=True)
d = ms.Midi(0, 1)
try:
    e0 = dm.read_edit_buffer(d)
    open('work/dumps/backup_before_write_%s.syx' % time.strftime('%H%M%S'), 'wb').write(e0)
    p0 = dm.parse_edit_buffer(e0)
    print('etat initial : nom=%r, octet34=%d' % (bytes(p0[223:239]).decode(), p0[34]))
    print('reconstruction hors ligne identique :', dm.build_edit_buffer(p0, 0) == e0)

    dm.write_edit_buffer(d, p0, confirm=dm.CONFIRM)
    e1 = dm.read_edit_buffer(d)
    print('2) renvoi identique -> relecture identique :', e1 == e0)

    p1 = bytearray(p0)
    p1[34] = (p0[34] + 3) if p0[34] < 250 else (p0[34] - 3)
    dm.write_edit_buffer(d, bytes(p1), confirm=dm.CONFIRM)
    e2 = dm.read_edit_buffer(d)
    p2 = dm.parse_edit_buffer(e2)
    diff = [i for i in range(242) if p2[i] != p0[i]]
    print('3) octets differents apres modification :', diff, '| octet34 =', p2[34], '(attendu %d)' % p1[34])
finally:
    try:
        dm.write_edit_buffer(d, p0, confirm=dm.CONFIRM)
        e3 = dm.read_edit_buffer(d)
        print('4) restauration -> identique a l\'etat initial :', e3 == e0)
    except Exception as ex:
        print('!! restauration impossible :', ex)
    d.close()
