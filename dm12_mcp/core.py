import os, sys, time, math, threading, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_safe as ms
import midi_dm12 as dm
import registry as R

HW_LOCK = threading.Lock()
BACKUP_DIR = os.path.join(ROOT, 'work', 'backups')
IN_DEV, OUT_DEV = None, None


def fx_slot_base(slot):
    return 166 + 13 * (slot - 1)


def step_to_physical(p, step):
    n = abs(p['steps']) - 1
    mn, mx = p['min'], p['max']
    if n <= 0:
        return mn
    if p['steps'] > 0 or mn <= 0:
        return mn + (mx - mn) * step / n
    return mn * (mx / mn) ** (step / n)


def physical_to_step(p, value):
    n = abs(p['steps']) - 1
    mn, mx = p['min'], p['max']
    if n <= 0:
        return 0
    if p['steps'] > 0 or mn <= 0:
        f = (value - mn) / (mx - mn)
    else:
        f = math.log(max(value, mn) / mn) / math.log(mx / mn)
    return max(0, min(n, int(round(f * n))))


def effect_by_name(x):
    if isinstance(x, int) or (isinstance(x, str) and x.isdigit()):
        return int(x)
    xl = str(x).strip().lower()
    for i, e in R.EFFECTS.items():
        if xl in (e['name'].lower(), e['short'].lower(), (e['ctor_class'] or '').lower()):
            return i
    raise ValueError('effet inconnu: %r' % (x,))


def label_index(labels, x, what):
    if isinstance(x, int) or (isinstance(x, str) and x.isdigit()):
        return int(x)
    xl = str(x).strip().lower()
    for i, l in enumerate(labels):
        if l.lower() == xl:
            return i
    raise ValueError('%s inconnu: %r' % (what, x))


def decode(prog):
    out = {'name': bytes(prog[223:239]).decode('ascii', 'replace').rstrip(), 'params': {}, 'fx': [], 'mod_matrix': []}
    for key, r in R.REGISTRY.items():
        if key.startswith('mod') and key[3].isdigit():
            continue
        if key.startswith('fx') and key[2].isdigit() and key.endswith('level'):
            continue
        out['params'][key] = int(prog[r['index']])
    for s in range(1, 5):
        t = prog[fx_slot_base(s)]
        e = R.EFFECTS.get(t)
        slot = {'slot': s, 'type_id': int(t), 'type': e['name'] if e else '?', 'level': int(prog[218 + s - 1]), 'params': {}}
        if e:
            for k, p in enumerate(e['params']):
                st = prog[fx_slot_base(s) + 1 + k]
                slot['params'][p['name']] = {'step': int(st), 'value': round(step_to_physical(p, st), 3), 'steps': abs(p['steps']) - 1}
        out['fx'].append(slot)
    for k in range(8):
        i = 93 + 3 * k
        out['mod_matrix'].append({'slot': k + 1, 'source': int(prog[i]), 'source_name': R.SOURCE_LABELS[prog[i]] if prog[i] < 25 else '?',
                                  'dest': int(prog[i + 1]), 'dest_name': R.DEST_LABELS[prog[i + 1]] if prog[i + 1] < 133 else '?',
                                  'depth': int(prog[i + 2])})
    known = set(r['index'] for r in R.REGISTRY.values()) | set(range(93, 117)) | set(range(166, 223)) | set(range(223, 239))
    out['unmapped_bytes_preserved'] = {i: int(prog[i]) for i in range(242) if i not in known}
    return out


def apply_changes(prog, changes, allow_risky=False):
    p = bytearray(prog)
    rep = {'applied': [], 'warnings': [], 'errors': [], 'risky_blocked': []}
    keys = sorted(changes, key=lambda k: (0 if k.endswith('.type') else 1, k))
    for key in keys:
        val = changes[key]
        try:
            if key == 'name':
                s = str(val)
                if len(s) > 16 or any(ord(c) < 0x20 or ord(c) > 0x7E for c in s):
                    raise ValueError('nom: 16 caracteres ASCII imprimables max')
                p[223:239] = s.ljust(16).encode('ascii')
                rep['applied'].append((key, s))
            elif key[:2] == 'fx' and key[2:3].isdigit() and key[3] == '.' and key[4:] == 'type':
                s = int(key[2]); t = effect_by_name(val)
                if not (0 <= t <= 35):
                    raise ValueError('type 0..35')
                p[fx_slot_base(s)] = t
                for k in range(12):
                    p[fx_slot_base(s) + 1 + k] = 0
                if t:
                    for k, prm in enumerate(R.EFFECTS[t]['params']):
                        d = prm['default_step']
                        p[fx_slot_base(s) + 1 + k] = min(d, abs(prm['steps']) - 1)
                rep['applied'].append((key, R.EFFECTS[t]['name']))
                rep['warnings'].append('fx%d: parametres remis aux valeurs par defaut de %s' % (s, R.EFFECTS[t]['name']))
            elif key[:2] == 'fx' and key[2:3].isdigit() and key[3] == '.' and key[4:] != 'level':
                s = int(key[2]); nm = key[4:]
                raw = nm.endswith('@step'); nm = nm[:-5] if raw else nm
                t = p[fx_slot_base(s)]
                e = R.EFFECTS.get(t)
                if not e or not t:
                    raise ValueError('slot %d sans effet' % s)
                idx = next((k for k, prm in enumerate(e['params']) if prm['name'].lower() == nm.lower() or prm['short'].lower() == nm.lower()), None)
                if idx is None:
                    raise ValueError('%s: parametres possibles: %s' % (e['name'], [q['name'] for q in e['params']]))
                prm = e['params'][idx]
                st = int(val) if raw else physical_to_step(prm, float(val))
                if not 0 <= st <= abs(prm['steps']) - 1:
                    raise ValueError('pas hors plage 0..%d' % (abs(prm['steps']) - 1))
                nm_l = prm['name'].lower(); frac = st / max(1, abs(prm['steps']) - 1); phys = step_to_physical(prm, st)
                risky = None
                if 'gain' in nm_l and prm['min'] < 0 and phys > 0:
                    risky = 'gain %s.%s = %+.1f dB (> 0 dB)' % (e['name'], prm['name'], phys)
                elif 'feedback' in nm_l and abs(phys) > 0.7 * max(abs(prm['min']), abs(prm['max'])):
                    risky = 'feedback %s.%s = %.0f (> 70 %% de la plage)' % (e['name'], prm['name'], phys)
                elif 'reso' in nm_l and frac > 0.8:
                    risky = 'resonance %s.%s > 80 %% de la plage' % (e['name'], prm['name'])
                elif 'drive' in nm_l and frac > 0.5:
                    risky = 'drive %s.%s > 50 %% de la plage' % (e['name'], prm['name'])
                if risky and not allow_risky:
                    rep['risky_blocked'].append((key, risky)); continue
                p[fx_slot_base(s) + 1 + idx] = st
                rep['applied'].append((key, '%s = %.3f (pas %d)' % (prm['name'], phys, st)))
            elif key in R.REGISTRY:
                r = R.REGISTRY[key]
                if key.endswith('.source') and key.startswith('mod'):
                    v = label_index(R.SOURCE_LABELS, val, 'source')
                elif key.endswith('.dest') and key.startswith('mod'):
                    v = label_index(R.DEST_LABELS, val, 'destination')
                else:
                    v = int(round(float(val)))
                if not 0 <= v <= r['max']:
                    raise ValueError('%s: %d hors plage 0..%d' % (key, v, r['max']))
                limit = R.SOFT_LIMITS.get(key)
                if key.endswith('.level') and key.startswith('fx'):
                    limit = R.FX_LEVEL_SOFT
                if limit is not None and v > limit and not allow_risky:
                    rep['risky_blocked'].append((key, '%s = %d > seuil de securite %d' % (key, v, limit))); continue
                p[r['index']] = v
                rep['applied'].append((key, v))
            else:
                raise ValueError('parametre inconnu: %r' % key)
        except Exception as ex:
            rep['errors'].append((key, str(ex)))
    rep['validation'] = dm.validate_program(bytes(p))
    return bytes(p), rep


def _open():
    global IN_DEV, OUT_DEV
    return ms.Midi(0, 1)


def hw_read():
    with HW_LOCK:
        d = _open()
        try:
            raw = dm.read_edit_buffer(d)
        finally:
            d.close()
    return raw, dm.parse_edit_buffer(raw)


def hw_identity():
    with HW_LOCK:
        d = _open()
        try:
            d.take(0.3)
            d.send_sysex(bytes([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7]))
            for r in d.take(1.5):
                if r[0] == 0xF0 and len(r) >= 17 and r[1] == 0x7E:
                    return r
        finally:
            d.close()
    return None


def backup(raw, tag='manual'):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    fn = os.path.join(BACKUP_DIR, 'edit_buffer_%s_%s.syx' % (datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), tag))
    open(fn, 'wb').write(raw)
    return os.path.basename(fn)


def hw_write(prog, allow_backup=True):
    with HW_LOCK:
        d = _open()
        try:
            raw0 = dm.read_edit_buffer(d)
            bk = backup(raw0, 'before_write') if allow_backup else None
            dm.write_edit_buffer(d, prog, confirm=dm.CONFIRM)
            raw1 = dm.read_edit_buffer(d)
        finally:
            d.close()
    p1 = dm.parse_edit_buffer(raw1)
    diff = [(i, prog[i], p1[i]) for i in range(242) if prog[i] != p1[i]]
    return {'backup': bk, 'readback_identical': not diff, 'differences': diff}
