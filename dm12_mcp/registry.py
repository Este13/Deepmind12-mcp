import os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_P = json.load(open(os.path.join(ROOT, 'params.json'), encoding='utf-8'))
DEFAULT = bytes.fromhex(_P['program_layout']['default_program_bytes_hex'])
DEST_LABELS = _P['label_tables']['pointer_table_0x14086e9b0']['labels'][:133]
SOURCE_LABELS = ["None", "Pitch Bend", "Mod Wheel", "Foot Ctrl", "BreathCtrl", "Pressure", "LFO 1", "LFO 2", "Env 1", "Env 2", "Env 3",
                 "Note Num", "Note Vel", "Ctrl Seq", "LFO1 (uni)", "LFO2 (uni)", "LFO1 Fade", "LFO2 Fade", "NoteOffVel", "Voice Num",
                 "CC X(115)", "CC Y(116)", "CC Z(117)", "Uni Voice", "Expression"]
EFFECTS = {e['id']: e for e in _P['effects']['list']}

_R = []


def add(key, idx, desc, mx=255, ev='hw'):
    _R.append(dict(key=key, index=idx, desc=desc, max=mx, ev=ev, default=DEFAULT[idx], section=key.split('.')[0]))


for n, base in (('lfo1', 0), ('lfo2', 7)):
    add(f'{n}.rate', base, 'LFO rate')
    add(f'{n}.delay', base + 1, 'LFO delay time')
    add(f'{n}.shape', base + 2, 'LFO shape 0..6 (7 formes ; ordre des libelles non verifie)', 6, 'hw+bin' if n == 'lfo1' else 'hw')
    add(f'{n}.key_sync', base + 3, 'LFO key sync (0/1)', 1)
    add(f'{n}.arp_sync', base + 4, 'LFO arp sync (0/1)', 1)
    add(f'{n}.phase', base + 5, 'LFO phase')
    add(f'{n}.slew_rate', base + 6, 'LFO slew rate')

add('osc1.range', 14, 'OSC1 range 0..2 (16\'/8\'/4\' ; ordre non verifie)', 2, 'hw+bin')
add('osc1.pulse_on', 18, 'OSC1 pulse (bouton, 0/1)', 1)
add('osc1.saw_on', 19, 'OSC1 saw (bouton, 0/1)', 1)
add('osc1.pitch_mod', 21, 'OSC1 pitch mod amount')
add('osc1.pmod_src', 22, 'OSC1 P.MOD-SRC 0..6 (source de mod. de pitch)', 6, 'hw+bin')
add('osc1.aft_pmod', 23, 'OSC1 AFT>P.MOD')
add('osc1.wheel_pmod', 24, 'OSC1 WHEEL>P.MOD')
add('osc1.pwm', 25, 'OSC1 PWM')
add('osc1.aux_src', 16, 'OSC1 ligne 5 de la page EDIT (0..5 ; libelle non lu)', 5, 'hw+bin')
add('osc1.aux_mode', 38, 'OSC1 ligne 6 de la page EDIT (0/1 ; libelle non lu)', 1, 'hw+bin')
add('osc1.key_dn_reset', 92, 'OSC1 KEY-DN-RESET (0/1)', 1, 'hw+bin')
add('osc2.range', 15, 'OSC2 range 0..2', 2, 'hw+bin')
add('osc2.sync', 20, 'OSC2 sync (bouton, 0/1)', 1)
add('osc2.level', 26, 'OSC2 level')
add('osc2.pitch', 27, 'OSC2 pitch')
add('osc2.tone_mod', 28, 'OSC2 tone mod')
add('osc2.pitch_mod', 29, 'OSC2 pitch mod amount')
add('osc2.aft_pmod', 30, 'OSC2 AFT>P.MOD')
add('osc2.wheel_pmod', 31, 'OSC2 WHEEL>P.MOD')
add('osc2.pmod_src', 32, 'OSC2 P.MOD-SRC 0..6', 6, 'hw+bin')
add('osc2.tmod_src', 17, 'OSC2 T.MOD-SRC 0..5', 5, 'hw+bin')
add('noise.level', 33, 'Noise level')

add('porta.time', 34, 'Portamento time')
add('porta.mode', 35, 'PORTA-MODE 0..13 (14 modes)', 13, 'hw+bin')
add('porta.osc_bal', 91, 'PORTA-OSC-BAL')
add('pitch.bend_up', 36, 'P.BEND-RANGE+ 0..48 (demi-tons)', 48, 'hw+bin')
add('pitch.bend_down', 37, 'P.BEND-RANGE- 0..48 (demi-tons)', 48, 'hw+bin')
add('pitch.transpose', 241, 'TRANSPOSE (centre 128 ; plage vue 80..176)', 255, 'hw')

add('vcf.cutoff', 39, 'VCF frequency (cutoff)')
add('vcf.resonance', 41, 'VCF resonance (0..255, pas de limite logicielle ; auto-oscillation possible)')
add('vcf.env_amount', 42, 'VCF envelope amount')
add('vcf.lfo_amount', 45, 'VCF LFO amount')
add('vcf.keyboard', 49, 'VCF keyboard tracking')
add('vcf.velocity_sens', 43, 'VCF velocity sensitivity')
add('vcf.pbend_freq', 44, 'VCF pitch-bend > freq')
add('vcf.lfo_select', 46, 'VCF LFO-SELECT (0=LFO-1, 1=LFO-2)', 1, 'hw+bin')
add('vcf.aft_lfo_depth', 47, 'VCF AFT-LFO-DEPTH')
add('vcf.mw_lfo_depth', 48, 'VCF MW-LFO-DEPTH')
add('vcf.invert', 50, 'VCF invert (bouton, 0/1)', 1)
add('vcf.lpf_type', 51, 'LPF-TYPE (bouton 2 POLE ; 0/1)', 1)
add('hpf.freq', 40, 'HPF frequency')
add('hpf.boost', 52, 'BASS-BOOST (bouton BOOST, 0/1)', 1)
add('vca.level', 80, 'VCA level')
add('vca.env_depth', 81, 'VCA ENVELOPE-DEPTH')
add('vca.velocity_sens', 82, 'VCA VELOCITY-SENS')
add('vca.pan_spread', 83, 'VCA PAN-SPREAD')

add('voice.priority', 84, 'PRIORITY 0..2 (Lowest/Highest/Last)', 2, 'hw+bin')
add('voice.polyphony', 85, 'POLYPHONY 0..12 (13 modes Poly/Unison/Mono...)', 12, 'hw+bin')
add('voice.env_trigger', 86, 'ENV-TRIGGER 0..3', 3, 'hw+bin')
add('voice.unison_detune', 87, 'UNISON-DETUNE')
add('voice.osc_drift', 88, 'OSC-DRIFT')
add('voice.param_drift', 89, 'PARAM-DRIFT')
add('voice.drift_rate', 90, 'DRIFT-RATE')

for env, base in (('env_vca', 53), ('env_vcf', 62), ('env_mod', 71)):
    for i, nm in enumerate(('attack', 'decay', 'sustain', 'release')):
        add(f'{env}.{nm}', base + i, f'{env} {nm}')
        add(f'{env}.{nm}_curve', base + 5 + i, f'{env} {nm} curve')

add('arp.on', 155, 'ARP on/off (0/1)', 1, 'hw+bin')
add('arp.mode', 156, 'ARP MODE 0..10 (11 modes ; ordre non verifie)', 10, 'hw+bin')
add('arp.rate', 157, 'ARP rate (BPM raw)')
add('arp.clock_div', 158, 'ARP CLOCK DIVIDER 0..12', 12, 'hw+bin')
add('arp.key_sync', 159, 'ARP KEY-SYNC (0/1)', 1, 'hw+bin')
add('arp.gate', 160, 'ARP gate time')
add('arp.hold', 161, 'ARP HOLD (0/1)', 1, 'hw+bin')
add('arp.pattern', 162, 'ARP PATTERN 0..64', 64, 'hw+bin')
add('arp.swing', 163, 'ARP SWING 0..25 (affiche 50..75)', 25, 'hw+bin')
add('arp.octave', 164, 'ARP OCT 0..5', 5, 'hw+bin')
add('fx.routing', 165, 'FX routing 0..9 (borne binaire ; non observe)', 9, 'bin')
add('fx.mode', 222, 'FX OVERVIEW ligne du haut (Insert...) 0..2', 2, 'hw+bin')
for s in range(4):
    add(f'fx{s + 1}.level', 218 + s, f'FX{s + 1} level (0..150 ; 100 = nominal)', 150, 'hw+bin')

add('cseq.enable', 117, 'CTRL SEQ ENABLE (0/1)', 1, 'hw+bin')
add('cseq.clock_div', 118, 'CTRL SEQ CLOCK DIVIDER 0..19', 19, 'hw+bin')
add('cseq.length', 119, 'CTRL SEQ LENGTH 0..30', 30, 'hw+bin')
add('cseq.swing', 120, 'CTRL SEQ SWING 0..25', 25, 'hw+bin')
add('cseq.key_loop', 121, 'CTRL SEQ KEY/LOOP 0..2', 2, 'hw+bin')
add('cseq.slew_rate', 122, 'CTRL SEQ SLEW-RATE')

for k in range(8):
    add(f'mod{k + 1}.source', 93 + 3 * k, f'Mod matrix slot {k + 1} source 0..24 (ou nom)', 24, 'hw+bin' if k in (0, 1, 7) else 'bin')
    add(f'mod{k + 1}.dest', 94 + 3 * k, f'Mod matrix slot {k + 1} destination 0..132 (ou nom)', 132, 'hw+bin' if k in (0, 1, 7) else 'bin')
    add(f'mod{k + 1}.depth', 95 + 3 * k, f'Mod matrix slot {k + 1} depth (128 = 0)', 255, 'hw+bin' if k in (0, 1, 7) else 'bin')

REGISTRY = {r['key']: r for r in _R}
BY_INDEX = {}
for r in _R:
    BY_INDEX[r['index']] = r

SOFT_CAPS = [('gain', 0.0, 'dB'), ('feedback', 70.0, '%'), ('reso', 80.0, '%'), ('drive', 50.0, '%')]
SOFT_LIMITS = {'vcf.resonance': 220}
FX_LEVEL_SOFT = 100
