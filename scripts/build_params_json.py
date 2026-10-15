import json, struct
d = open('work/DeepMind12.exe', 'rb').read()
RD_VA, RD_OFF = 0x1404d7000, 0x4d5800
off = lambda va: va - RD_VA + RD_OFF
def cstr(va, mx=40):
    if not (RD_VA <= va < RD_VA + 0x17e9a00): return None
    o = off(va); e = d.find(b'\0', o, o + mx + 1)
    if e <= o: return None
    t = d[o:e]
    return t.decode('latin1') if all(32 <= c < 127 for c in t) else None

prog = list(d[off(0x14051f570):off(0x14051f570) + 242])
labels, va = [], 0x14086e9b0
while True:
    q, = struct.unpack_from('<Q', d, off(va)); s = cstr(q)
    if s is None: break
    labels.append(s); va += 8
def tbl(start, n):
    return [cstr(struct.unpack_from('<Q', d, off(start + 8 * i))[0]) for i in range(n)]

out = {
 "_meta": {
  "source": "DeepMind12.exe sha256 f467b984b1e25e7ce3bca06fd1e388348c801f6015a0b2db12878f763c9a01c3 (analyse statique, Ghidra 12.1.4)",
  "status": "Statique + verification materiel (firmware 1.1.2-619). Voir notes/ ; noms des parametres : section named_controls_observed_on_hardware ; registre pilotable du MCP : dm12_mcp/registry.py. Reste sans nom : octets 57, 66, 75 (5e octet des enveloppes) ; Globals hors perimetre."
 },
 "nrpn_to_program_byte": {
  "function": "0x14035bf30 (Phat12Synth::addressOfParameter, prouve par decompilation + chaine 0x14051be38)",
  "note": "Chaque NRPN adresse UN octet d'un miroir dans l'objet Phat12Synth (offset objet indique). NRPN=(CC99<<7)|CC98 ; valeur = data LSB (CC38), voir setParameter 0x14035ba80.",
  "ranges": [
   {"nrpn_min": 0,   "nrpn_max": 241, "object_offset_start": "0x7c",  "layout": "octet n du programme de 242 octets (edit buffer)"},
   {"nrpn_min": 300, "nrpn_max": 354, "object_offset_start": "0x16e", "layout": "contigu apres le programme (semantique: unverified)"},
   {"nrpn_min": 356, "nrpn_max": 356, "object_offset_start": "0x206", "layout": "isole"},
   {"nrpn_min": 888, "nrpn_max": 888, "object_offset_start": "0x18c8", "layout": "isole"},
   {"nrpn_min": 889, "nrpn_max": 889, "object_offset_start": "0x18e0", "layout": "isole"},
   {"nrpn_min": 891, "nrpn_max": 955, "object_offset_start": "0x1a5",  "layout": "0x1a5 + (nrpn-891) (chevauche visuellement 300..354 -> 0x16e..0x1a4; 891.. commence en 0x1a5: contigu)"}],
  "out_of_range": "toute autre valeur => log 'Trying to access NRPN out of scope' et adresse NULL (rejet)",
  "value_storage": "1 octet (troncature du 14 bits recu, handleIncomingNRPN 0x140357370)"
 },
 "program_layout": {
  "size_bytes": 242,
  "evidence": "0x14035bf30 borne 0..0xF1 ; boucle memcpy 0xF2 octets x 128 programmes dans 0x140365920 (0x14051f570 = programme par defaut, getter 0x140357530)",
  "name_field": {"offset": 223, "length": 16, "encoding": "ascii NUL-padded (deduit du programme par defaut: 'Default Program')"},
  "default_program_bytes_hex": bytes(prog).hex(),
  "default_program_name": bytes(prog[223:239]).split(b'\0')[0].decode(),
  "default_program_va": "0x14051f570"
 },
 "ui_bindings": {
  "note": "NRPN passes en constante aux fonctions de creation de Binding (wrappers 0x1402114f0=slider<int>, 0x1402115b0=slider<uchar>, 0x14035b3f0=callback, 0x14035b500=button). nrpn=null => valeur calculee (boucle/indice), non resolue. Le NOM du controle n'est pas dans ces appels.",
  "entries": json.load(open('work/bindings.json'))
 },
 "effects": {
  "note": "Table de 36 effets (id 0..35) a 0x140522f20 (structs 0x28) ; parametres : structs 0x38. Structures et plage 0..abs(steps)-1 PROUVEES par decompilation (FUN_1404743e0 @0x1404743e0, FUN_140474b50 = ctor VintageRoom passant le descripteur a FUN_140230070). Semantique de a/kind/class_byte et du champ default_step: unverified (2 defaults hors plage dans la source : Plate Reverb/Size, DualPitch/Gain2).",
  "nrpn_of_effect_param": "FUN_14024d950 @0x14024d950 : slot 0..3 -> base 167,180,193,206 ; NRPN = base + index_param (PROUVE). Selecteur de type d'effet par slot = base-1 = 166,179,192,205 (bindings de ces 4 NRPN, valeur = id d'effet 0..35 : INFERE, unverified).",
  "list": json.load(open('work/effects.json'))
 },
 "sections_nrpn": {
  "note": "NRPN passes en constante aux Bindings, regroupes par classe UI. Provenance : callers des wrappers de binding + vftable/ctor. Les NOMS de parametres ne sont pas dans le binaire (UI a base d'images) => pas de nom.",
  "VCFSection (ctor 0x140463a20)": [39, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51],
  "DCO1Section (bind 0x140465860)": [14, 16, 18, 19, 20, 21, 22, 23, 24, 25, 38],
  "DCO2Section (0x14046d790)": [15, 17, 26, 27, 28, 29, 30, 31, 32, 33],
  "VCAHPFSection (0x14046b3c0)": [40, 52, 80, 81, 82, 83, 347],
  "PortamentoSection (bind 0x14045c6c0)": [34, 35, 36, 37, 84, 85, 86, 87, 88, 89, 90, 91, 241, 331],
  "shared base 0x140466fb0 (appelee par DCO1/LFO..)": [94, 97, 100, 103, 106, 109, 112, 115],
  "ArpeggiatorSection (0x14049beb0)": [155, 156, 157, 158, 159, 160, 163, 891],
  "ControlSequencerSection (0x14049d370)": [117, 118, 119, 120, 121, 122],
  "page globale 0x1404247a0": [155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 891],
  "EffectsSection routing (0x14049e790)": [165, 222],
  "effets: types + params": "voir effects.nrpn_of_effect_param",
  "0x140445ee0": [300, 301, 338, 345], "0x14044f220": [302, 304, 305, 306, 307, 308, 309, 310, 312, 313, 314, 315, 316, 317, 319, 320, 321, 322, 323, 324], "0x140452930": [332, 333, 346, 348, 349, 350, 351, 352, 353, 354],
  "StatusBar VoicesDisplay (0x140437c10)": [356]
 },
 "default_slider_range": {"value": [0, 255], "step": 1, "evidence": "Phat12Slider ctor FUN_14043ef70 @0x14043ef70 : FUN_140210be0(0,0xff). Aucune plage plus fine n'est posee pour les sections principales dans les ctors examines (VCFSection 0x140463a20) : les plages reelles par parametre sont donc INCONNUES cote editeur (unverified) ; controle uchar par FUN_140212050 @0x140212050 clampe a [min,max] du controle."},
 "label_tables": {
  "pointer_table_0x14086e9b0": {"note": "getter FUN_14043a1b0 (index -> label) ; probablement destinations de la mod matrix (unverified)", "labels": labels},
 }
}

lim = []
for i in range(0x48):
    idx, mx, _ = struct.unpack_from('<HBB', d, off(0x140522720) + 4 * i)
    lim.append({"nrpn_or_byte_index": idx, "max": mx, "default": prog[idx]})
out["value_limits_on_receive"] = {
  "evidence": "FUN_140406000 @0x140406000 (appelee apres depack d'un programme recu, dans handleProgramDumpResponse 0x140358fe0 et handleEditBufferDump 0x140359330) : pour chacune des 72 entrees {u16 index, u8 max, u8 pad} a 0x140522720, si octet[index] > max alors octet[index] = valeur du programme par defaut (0x14051f570). Puis octet[0x55] passe par FUN_140404b70. Les parametres absents de cette table ne sont PAS bornes par ce code.",
  "entries": lim,
  "signed_pitch_bytes": {"indexes": [36, 37], "wire_conversion": "FUN_140404fe0 @0x140404fe0 (emission) : octet = clamp(v-24, -24, +24) en signe ; FUN_140405bd0 @0x140405bd0 (reception) : v = clamp(signed+24, 0, 48). (semantique 'pitch OSC' non prouvee)"}
}
out["nrpn_blocks"] = {
  "0..241": "programme de 242 octets (edit buffer)",
  "300..354": "55 octets 'Globals' (dump SysEx cmd 6, 0x37 octets, FUN_140359450 @0x140359450); NRPN 302 = device id (FUN_14035c720/760)",
  "891..955": "65 octets 'Edit Pattern' (dump SysEx cmd 0xF, 0x41 octets, FUN_140358a90 @0x140358a90)",
}

gmx = d[off(0x1405216e8):off(0x1405216e8) + 55]; gdf = d[off(0x1405224e8):off(0x1405224e8) + 55]
out["globals_limits_on_receive"] = {
  "evidence": "FUN_1404060c0 @0x1404060c0 (appelee par handler GlobalsDumpResponse FUN_140359450) : 55 octets (NRPN 300..354), max = table 0x1405216e8, valeur de repli = table 0x1405224e8.",
  "entries": [{"nrpn": 300 + i, "max": gmx[i], "default": gdf[i]} for i in range(55)]
}
out["pattern_limits_on_receive"] = {
  "evidence": "FUN_140405ef0 @0x140405ef0 (EditPatternDumpResponse, 65 octets = NRPN 891..955) : octet0 <= 0x1f ; octets 1..32 <= 0x7f ; octets 33..64 <= 0x80 (clamp, pas de repli)."
}

import csv
named = []
for r in csv.DictReader(open('notes/named_params.csv', encoding='utf-8')):
    named.append(r)
out["named_controls_observed_on_hardware"] = {
  "source": "ecoute passive MIDI du synthe reel (scripts/midi_listen_ctrl.py, notes/hardware_check.md) ; chaque ligne = un potard/bouton bouge seul ou dans un ordre annonce.",
  "value_format": "NRPN 14 bits : CC99=n>>7, CC98=n&0x7F, CC6=v>>7, CC38=v&0x7F ; potards 0..255",
  "entries": named
}
json.dump(out, open('params.json', 'w'), indent=1)
print('ok', len(labels), 'labels', bytes(prog[223:239]))
