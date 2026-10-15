import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
import registry as R
from mcp.server import MCPServer

GUIDE = """DeepMind 12 : creation de presets sure.
Flux conseille : 1) dm12_status  2) dm12_read_patch (etat courant)  3) dm12_list_parameters / dm12_list_effects
4) dm12_preview_changes (aucun envoi)  5) dm12_apply_changes(dry_run=false, confirm='EDIT_BUFFER_ONLY').
Regles : les valeurs vont de 0 a 255 (max plus bas pour les interrupteurs/enums, cf. dm12_list_parameters) ;
les parametres d'effet se donnent en unite physique (ms, dB, %...) ; source/destination de mod matrix acceptent un nom ou un index.
Securite : tout est ecrit dans l'edit buffer (volatil) et l'etat precedent est sauvegarde (dm12_list_backups / dm12_restore_backup).
Les valeurs 'risquees' (resonance > 220, FX level > 100, gain > 0 dB, feedback > 70 %, reso/drive eleves) sont BLOQUEES tant que
allow_risky n'est pas passe explicitement a true ; baisse le volume du synthe avant de tester.
Pour SAUVEGARDER definitivement un preset, l'utilisateur doit le faire lui-meme sur le synthe (bouton WRITE) : ce serveur ne touche jamais la flash."""

server = MCPServer('deepmind12', instructions=GUIDE)


def _prog_or_default(base):
    if base == 'default':
        return R.DEFAULT
    raw, prog = core.hw_read()
    return prog


@server.tool()
def dm12_status() -> dict:
    idr = core.hw_identity()
    return {'connected': idr is not None, 'identity_reply': idr.hex(' ') if idr else None,
            'expected_identity': 'f0 7e <id> 06 02 00 20 32 20 00 01 00 ...',
            'firmware_tested': '1.1.2-619',
            'scope': 'edit buffer (volatile) only; never flash, never Globals, never firmware/calibration'}


@server.tool()
def dm12_read_patch() -> dict:
    raw, prog = core.hw_read()
    d = core.decode(prog)
    d['raw_hex'] = bytes(prog).hex()
    return d


@server.tool()
def dm12_list_parameters(section: str = '') -> dict:
    rows = [{'key': r['key'], 'desc': r['desc'], 'max': r['max'], 'default': r['default'], 'evidence': r['ev']}
            for r in R.REGISTRY.values() if not section or r['section'] == section]
    return {'count': len(rows), 'parameters': rows,
            'evidence_legend': {'hw': 'verifie sur le materiel', 'bin': 'borne lue dans l\'editeur officiel', 'hw+bin': 'les deux'},
            'other': ['name (16 caracteres ASCII)', 'fxN.type (nom ou id 0..35)', 'fxN.<parametre d\'effet> (unite physique)', 'modN.source / modN.dest (nom ou index)']}


@server.tool()
def dm12_list_effects(effect: str = '') -> dict:
    if not effect:
        return {'effects': [{'id': i, 'name': e['name'], 'short': e['short'], 'n_params': e['n_params']} for i, e in R.EFFECTS.items()]}
    t = core.effect_by_name(effect)
    e = R.EFFECTS[t]
    return {'id': t, 'name': e['name'], 'params': [{'name': p['name'], 'short': p['short'], 'min': p['min'], 'max': p['max'],
                                                   'steps': abs(p['steps']), 'scale': 'log' if p['steps'] < 0 and p['min'] > 0 else 'lin',
                                                   'default_physical': round(core.step_to_physical(p, min(p['default_step'], abs(p['steps']) - 1)), 3),
                                                   'fmt': p['fmt']} for p in e['params']]}


@server.tool()
def dm12_list_modulation() -> dict:
    return {'sources': R.SOURCE_LABELS, 'destinations': R.DEST_LABELS,
            'note': "depth 128 = pas de modulation ; l'ordre des libelles n'est verifie sur materiel que pour quelques index"}


def _preview(base, changes, allow_risky):
    prog = _prog_or_default(base)
    new, rep = core.apply_changes(prog, changes, allow_risky)
    return prog, new, rep


@server.tool()
def dm12_preview_changes(changes: dict, base: str = 'current', allow_risky: bool = False) -> dict:
    prog, new, rep = _preview(base, changes, allow_risky)
    rep['changed_bytes'] = [(i, prog[i], new[i]) for i in range(242) if prog[i] != new[i]]
    rep['ok_to_write'] = not rep['errors'] and not rep['validation'] and not rep['risky_blocked']
    return rep


@server.tool()
def dm12_apply_changes(changes: dict, base: str = 'current', dry_run: bool = True, confirm: str = '', allow_risky: bool = False) -> dict:
    prog, new, rep = _preview(base, changes, allow_risky)
    rep['changed_bytes'] = [(i, prog[i], new[i]) for i in range(242) if prog[i] != new[i]]
    if rep['errors'] or rep['validation'] or rep['risky_blocked']:
        rep['written'] = False
        rep['reason'] = 'erreurs, validation ou valeurs risquees : rien ecrit'
        return rep
    if dry_run:
        rep['written'] = False
        rep['reason'] = 'dry_run'
        return rep
    if confirm != 'EDIT_BUFFER_ONLY':
        rep['written'] = False
        rep['reason'] = "confirm manquant (doit valoir 'EDIT_BUFFER_ONLY')"
        return rep
    res = core.hw_write(new)
    rep['written'] = True
    rep.update(res)
    return rep


@server.tool()
def dm12_list_backups() -> dict:
    os.makedirs(core.BACKUP_DIR, exist_ok=True)
    return {'backups': sorted(os.listdir(core.BACKUP_DIR))}


@server.tool()
def dm12_restore_backup(filename: str, confirm: str = '') -> dict:
    if confirm != 'EDIT_BUFFER_ONLY':
        return {'restored': False, 'reason': "confirm manquant (doit valoir 'EDIT_BUFFER_ONLY')"}
    fn = os.path.join(core.BACKUP_DIR, os.path.basename(filename))
    if not os.path.isfile(fn):
        return {'restored': False, 'reason': 'sauvegarde introuvable'}
    prog = core.dm.parse_edit_buffer(open(fn, 'rb').read())
    res = core.hw_write(prog)
    return {'restored': True, **res}


if __name__ == '__main__':
    server.run('stdio')
