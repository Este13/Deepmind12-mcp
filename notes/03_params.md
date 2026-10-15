# Tâche 3 — Table des paramètres (état : PARTIEL)

Livrable : [`params.json`](../params.json) (régénérable : `python scripts/build_params_json.py`). Scripts : `XrefDecompile.java`, `Callers.java`, `RefsInRange.java`, `SymSearch.java`, `parse_fx_table.py`, `build_params_json.py`.

## Confirmé (décompilation)

### 1. NRPN -> octet (Phat12Synth::addressOfParameter, `FUN_14035bf30`)
Le log `Phat12Synth::addressOfParameter` (0x14051be38, ligne 0x24c de Phat12Synth.cpp) est émis par cette fonction. Elle renvoie un pointeur dans l'objet synthé :

| NRPN | offset dans l'objet |
|---|---|
| 0..241 (0xF1) | `0x7c + n` |
| 300..354 (0x12C..0x162) | `0x16e + (n-300)` |
| 356 (0x164) | `0x206` |
| 888 (0x378) / 889 (0x379) | `0x18c8` / `0x18e0` |
| 891..955 (0x37B..0x3BB) | `0x1a5 + (n-891)` |
| autre | NULL + log « Trying to access NRPN out of scope » |

Chaque NRPN = **1 octet** (miroir de l'état du synthé).

### 2. Envoi d'un paramètre (Phat12Synth::setParameter, `FUN_14035ba80`)
Si le miroir est valide, écrit `*ptr = (uint8)value`, puis (si le 4e argument ≠ 0) envoie **4 messages Control Change** sur le canal TX (`status = 0xB0 | (channel & 0xF)`, canal lu par `FUN_14035cac0`) :
1. CC 99 (0x63) = `nrpn >> 7` (NRPN MSB)
2. CC 98 (0x62) = `nrpn & 0x7F` (NRPN LSB)
3. CC 6 = `0` (Data Entry MSB)
4. CC 38 (0x26) = `value & 0x7F` (Data Entry LSB)

⇒ **Par NRPN on ne peut envoyer que 0..127** (LSB seul, MSB forcé à 0), alors que le miroir stocke un octet et que le programme par défaut contient des 0x80/0xFF. Les paramètres dont la plage dépasse 127 ne semblent donc pas atteignables par cette voie (*à valider avec `FUN_14035c280` = envoi et avec le firmware ; unverified*). Pas d'appel de « NRPN null / RPN reset » (CC 101/100) après l'envoi.

### 3. Réception (handleIncomingNRPN, `FUN_140357370`)
`nrpn = b[0x17d8]*128 + b[0x17d9]` ; `valeur = b[0x17da]*128 + b[0x17db]` (14 bits), puis stocke `(uint8)valeur` et notifie les listeners. Hors plage => log « Receiving out of scope NRPN » et rien n'est écrit. **Aucun clamp de la valeur** (troncature en octet) : point pour la tâche 6.

### 4. Le programme fait 242 octets, et NRPN 0..241 = index d'octet dans le programme
- Boucle `for i<0x80 { memcpy(prog_i, DEFAULT, 0xF2) }` dans `FUN_140365920` (0x140365920, ~ligne 111–121) ⇒ 128 programmes/banque de **0xF2 = 242 octets** (objet banque `operator_new(0x8138)`).
- `DEFAULT` = `FUN_140357530()` = `0x14051f570` : le programme d'init. Il se termine par `64 64 64 01` puis le nom **`Default Program`** en octets 223..238 (16 octets, NUL-terminé/paddé). Les octets 239..241 = `00 00 80`(*brut*).
- Le programme par défaut est dans `params.json > program_layout.default_program_bytes_hex` : **c'est la seule source de valeurs par défaut prouvée**.
- Remarque : les valeurs vont jusqu'à 0xFF et 0x80 apparaît souvent (centre de paramètres bipolaires ?) — interprétation *unverified*.
- Le nom du preset est donc dans la plage NRPN (octets 223..238), pas seulement dans le SysEx.

### 5. Bindings UI -> NRPN
Classes `Binding`, `ControlBinding<unsigned char>`, `ControlBinding<int>`, `ButtonBinding`, `CallbackBinding` (Bindings.h/.cpp). Wrappers de création : `0x1402114f0` (slider int), `0x1402115b0` (slider uchar), `0x14035b500` (bouton), `0x14035b3f0` (callback). 256 sites d'appel, **149 avec NRPN constant, 122 valeurs distinctes** entre 14 et 891 (dans `params.json > ui_bindings`, avec fonction UI appelante). Aucun nom de contrôle dans ces appels.

## Effets : RÉSOLU (prouvé par le code)
- **Table de 36 effets** à `0x140522f20` (structs 0x28 : `short*, name*, 1, nparams|id|class_byte, ptr params`), id 0 = None … 35 = VintagePitchShift ; associée à chaque classe `XxxEffectComponent` par son constructeur (`FUN_140230070` = ctor de base, reçoit ce pointeur en 2e argument ; liste dans `work/effect_ctors.txt`, script `EffectCtors.java`).
- **Paramètre** (0x38 octets, `ptr + 0x38*i`) : `min f32, max f32, steps i32, fmt*, a, default_step, name*, short*, kind`. Ma 1re lecture du tableau était décalée ; la bonne est confirmée par `FUN_1404743e0` (0x1404743e0) : `rec = effect.params + idx*0x38 ; range = FUN_140210be0(0, abs(rec.steps)-1)` ⇒ **la valeur octet d'un paramètre d'effet va de 0 à |steps|-1** (pas de 1), valeur physique = interpolation min..max (`steps<0` = échelle non linéaire, *unverified*).
- **NRPN d'un paramètre d'effet** : `FUN_14024d950` (0x14024d950) : `base(slot) + index`, base = 167 / 180 / 193 / 206 pour les slots FX1..FX4. Les NRPN 166 / 179 / 192 / 205 sont le **type d'effet** de chaque slot (valeur = id 0..35) — **confirmé par la table de bornes `0x140522720` : max = 35 pour ces 4 octets** (voir plus bas). 371 paramètres au total (dans `params.json > effects`).
- 2 valeurs par défaut dépassent leur plage dans les données d'origine (Plate Reverb/Size, DualPitch/Gain2) : signalées, non corrigées.

## Plages des paramètres principaux
- Le slider standard `Phat12Slider` (ctor `0x14043ef70`) est créé avec la plage **0..255, pas 1** (`FUN_140210be0(0,0xff)`) ; le contrôle uchar clampe à ses bornes (`FUN_140212050`, 0x140212050). Dans les constructeurs de sections examinés (VCFSection `0x140463a20`, etc.) aucune plage plus étroite n'est posée. ⇒ **côté éditeur, aucune table de plages fines par paramètre principal** ; les plages réelles (0..127 ? autres) relèvent du firmware (donc de la tâche 6 / à confirmer hors analyse statique).
- L'UI est skinnée par images (`*_png`) : **les libellés des paramètres principaux ne sont pas dans le binaire**, donc pas de nom. Ce que l'on peut prouver est le regroupement par section (`params.json > sections_nrpn`) : DCO1/DCO2/VCF/VCAHPF/Portamento/LFO/Arp/ControlSeq/Effets, avec les NRPN de chacune.
- Conséquence : le mapping octet↔nom pour NRPN 0..241 hors effets ne peut PAS être établi sans source externe (doc MIDI Behringer ou test matériel). Pas fait.

## Reste incertain (après résolution)
- Signification de `a`, `kind`, `class_byte`, du signe de `steps`.
- Classes de quelques fonctions de bindings (0x140445ee0, 0x14044f220, 0x140452930 : NRPN 300–354, probablement étendus/globaux ; non attribuées).

## Ajouts après la tâche 4 (prouvés)
- **Blocs NRPN** : 0..241 = programme (242 o.) ; **300..354 = 55 octets « Globals »** (SysEx cmd 6, `FUN_140359450`) ; **891..955 = 65 octets « Edit Pattern »** (cmd 0xF, `FUN_140358a90`). NRPN 302 = device id (`FUN_14035c720/760`). 
- **Table de bornes à la réception** `FUN_140406000` (0x140406000) : 72 entrées `{u16 index, u8 max}` à `0x140522720` ; hors borne -> valeur par défaut. Exemples : effets type (166,179,192,205) ≤ 35 ; niveaux FX (218..221) ≤ 150 ; octets 36/37 ≤ 48 ; 157 ≤ 255 ; 94/97/…/112 ≤ 132 ; 93/96/… ≤ 24 ; 162 ≤ 64 ; 118 ≤ 19, 119 ≤ 30, 120 ≤ 25. Contenu complet : `params.json > value_limits_on_receive`. **Ce sont les seules plages prouvées pour les paramètres principaux** (72 sur 242+55+65).
- Les octets 36 et 37 sont convertis en signé (v-24) sur le fil (`FUN_140404fe0` / `FUN_140405bd0`).

## Effets : confirmé sur matériel (ajout)
La table des effets est **validée sur le synthé réel** (voir `hardware_check.md`) : octet = pas, valeur physique linéaire ou exponentielle (signe de `steps`), NRPN = 167 + 13·slot + index. Reste non prouvé : signification de `a`, `kind`, `class_byte`, et l'échelle réelle du niveau FX (0..150).
