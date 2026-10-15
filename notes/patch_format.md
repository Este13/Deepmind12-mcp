# Tâche 5 — Format des patchs (fichier `.syx` de banque + programme de 242 octets)

Légende : **[P]** prouvé (code décompilé, adresse donnée) ; **[I]** inféré (recoupement défaut/bornes/bindings, à confirmer) ; **[?]** non vérifié.
Table complète octet par octet (défaut, borne, section UI, type de contrôle) : [`patch_map.csv`](patch_map.csv) (généré par `scripts/build_patch_map.py`).

## 1. Fichier banque `.syx` (LocalPresetBank)
- **Extension `.syx`** (0x14051c894 ; création `LocalPresetBank::createBank` `FUN_140365920`, copie `FUN_140368d70`). L'éditeur ne gère pas d'autre format de patch : `PresetManagerComponent::exportPreset` = « We don't currently support exporting Presets » (0x14052aa40) ; `getFileType` (`FUN_1404284f0`) logge « File type is unchecked - this could cause problems ».
- **Contenu** [P] : **128 enregistrements de 291 octets = 37 248 octets** (0x9180, tampon de `FUN_140367550` @0x140367550), un par programme, chacun étant **un message SysEx `ProgramDumpResponse` complet** (cf. `sysex.md` §4) :
  `F0 00 20 32 20 7F 02 07 00 <prog> <280 o. packés 7 bits> F7`
  - `7F` = device id « broadcast » (écrit par `FUN_140368260` @0x140368260 : `FUN_1404097a0(out, 0x7f, 0, prog, data)`) ;
  - `02` = commande ProgramDumpResponse ; `07` = version de format ; `00` = bank (toujours 0 dans un fichier) ; `<prog>` = numéro 0..127.
  - Les 128 enregistrements sont écrits dans l'ordre de l'index programme.
- **Lecture** (`LocalPresetBank::readFile`, lambda `FUN_1403651c0` @0x1403651c0) [P] :
  1. la taille du fichier doit être exactement `N × 0x123` (N = nombre de programmes de la banque, 128) sinon log « LocalPresetBank file is of an unusual size %db (should be %db) » et le fichier est **ignoré** ;
  2. pour chaque enregistrement : `prog = rec[9]` ; si `prog > 0x7F` seulement un **log** « Invalid program number in sysex file » (niveau 8) — le code **continue** ensuite avec ce numéro (pas de rejet : à traiter comme comportement défectueux, *ne pas s'y fier*) ;
  3. dépack via `FUN_140405cb0` (version = `rec[7]`, doit valoir 1..7 pour que la longueur attendue 0x123 corresponde), puis `FUN_140405bd0` (octets 36/37 : signé → non signé) puis `FUN_140406000` (bornes, cf. `params.json > value_limits_on_receive`).
  - **Non vérifiés par la lecture** : `F0`/`F7`, ID fabricant, device id, commande (`rec[6]`), `rec[8]` (bank) : aucun test trouvé [P : absence dans le lambda]. Un enregistrement de version invalide n'est pas dépacké (`FUN_140405cb0` renvoie faux, résultat ignoré) mais les post-traitements s'exécutent quand même sur un tampon non initialisé (*comportement à ne pas exploiter*).
- Banques flash du synthé : « Synth Bank A »…« H » (8 banques × 128 programmes). Une banque flash **ne peut pas être renommée** (0x141c158f8) ; `FlashPresetBank` = image de la mémoire du synthé, `LocalPresetBank` = fichier local.
- Envoi vers le synthé (`FUN_140366fe0` @0x140366fe0) [P] : pour chaque programme marqué modifié, envoie un `ProgramDumpResponse` (`FUN_14040a170`, dev = NRPN 302, `bank` de la banque courante, `prog` = index) **qui écrit directement dans la mémoire flash du synthé**, avec 200 ms entre deux envois. **C'est l'écriture de presets : opération destructive pour le programme cible.**

## 2. Programme (242 octets = 0xF2) [P]
Preuve : boucle de copie `0xF2 × 128` (`FUN_140365920`, ~l.111), `FUN_140405870` (longueur dépackée 0xF2 pour v2..7, 0xF0 pour v1), `FUN_140368b80` (accès programme n), valeur par défaut = `0x14051f570` (`FUN_140357530`).
**Octet n = NRPN n** (n = 0..241 ; `params.json > nrpn_to_program_byte`). Valeurs 8 bits (0..255 possibles ; bornes : seules 72 sont prouvées).

Programme par défaut (« Default Program », hex) :
```
  0: 00 00 01 00 00 00 00 00 00 01 00 00 00 00 01 01
 16: 00 00 01 01 00 00 00 00 00 00 00 00 00 00 00 00
 32: 00 00 00 05 02 02 00 ff 00 00 00 80 00 00 01 00
 48: 00 00 01 00 00 00 80 ff 80 00 80 00 80 00 00 80
 64: 80 80 00 80 00 80 00 00 80 80 80 00 80 00 80 00
 80: ff ff 80 80 02 00 00 00 00 00 00 80 00 00 00 80
 96: 00 00 80 00 00 80 00 00 80 00 00 80 00 00 80 00
112: 00 80 00 00 80 00 09 0e 00 02 00 80 80 80 80 80
128: 80 80 80 80 80 80 80 80 80 80 80 80 80 80 80 80
144: 80 80 80 80 80 80 80 80 80 80 80 00 00 78 09 01
160: 80 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00
176: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
192: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
208: 00 00 00 00 00 00 00 00 00 00 00 64 64 64 01 44
224: 65 66 61 75 6c 74 20 50 72 6f 67 72 61 6d 00 00
240: 00 80
```

### Plan des zones
| octets | contenu | statut / preuve |
|---|---|---|
| 0..13 | paramètres non regroupés par un binding (0–13 : pas de section UI ; bornes 2:6, 3:1, 4:1, 9:6, 10:1, 11:1) | [?] probablement oscillateurs/voix ; noms inconnus |
| 14..25, 38 | **DCO1Section** (bind `FUN_140465860`) | [P] groupe ; noms [?] |
| 15..17, 26..33 | **DCO2Section** (`FUN_14046d790`) | [P] groupe |
| 34..37, 84..91, 241, 331 | **PortamentoSection** (`FUN_14045c6c0`) ; 36/37 = pitch signé (fil : v−24 clampé ±24, max 48, défaut 2) | [P] groupe |
| 39, 41..51 | **VCFSection** (ctor `FUN_140463a20`) ; 39 défaut 0xFF (probable cutoff ouvert) | [P] groupe, [I] cutoff |
| 40, 52, 80..83, 347 | **VCAHPFSection** (`FUN_14046b3c0`) | [P] groupe |
| 53..79, 92 | non liés dans les sections lues (défauts 0x80/0xFF… : réglages bipolaires ; enveloppes/LFO probables) | [?] |
| 93..116 | **Matrice de modulation : 8 slots × 3 octets** `[source, destination, profondeur]` = `93+3k, 94+3k, 95+3k` (k=0..7) | [P] : bornes 24 (`93+3k`) et 132 (`94+3k`), migration v<4 remappe `0x5e+3k` (`FUN_1404054f0` @0x1404054f0) ; profondeur défaut 0x80 [I] |
| 117..122 | **ControlSequencerSection** (`FUN_14049d370`) ; bornes 117:1, 118:19, 119:30, 120:25, 121:2 | [P] groupe |
| 123..154 | 32 octets valant 0x80 par défaut : pas du séquenceur de contrôle | [I] |
| 155..165 | **Arpégiateur** (`FUN_14049beb0`, 155..160,163) ; 158 = « Arp clock » (max 12, clamp explicite `handleEditBufferDump` 0x140359330 : >12 ⇒ 12 et renvoi NRPN 158), 157 défaut 0x78=120 (BPM ?), 156 max 10 (mode ?), 165 max 9 = routage FX | [P] groupe et clamp ; rôles [I] |
| 166..217 | **4 slots d'effets × 13 octets** : `166+13s` = type d'effet (0..35, max 35 prouvé), puis 12 paramètres (`167+13s+i`) | [P] (`FUN_14024d950`, bornes) |
| 218..221 | niveaux FX 1..4 (max 150 ; défauts 0,100,100,100 aux octets 218..221 : 218=0 ; **[I]** : les octets 219..221 valent `64 64 64`) | bornes [P], rôle [I] |
| 222 | max 2 (routage/bypass ?), défaut 1 | [?] |
| 223..238 | **nom du programme, 16 octets ASCII, complété par NUL** (`Default Program\0`) | [P] (offset 0xDF lu dans `FUN_140358b40` : `+0xdf`, longueur 0x10) |
| 239..241 | 3 octets (défaut 00 00 80), 240 max 16 | [?] |

### Types d'effet (octet `166+13s`)
id 0 = None, 1 Hall, 2 Plate, 3 RichPlate, 4 Ambience, 5 Gated, 6 Reverse, 7 RackAmp, 8 MoodFilter, 9 Phaser, 10 Chorus, 11 Flanger, 12 ModDlyRev, 13 Delay, 14 3TapDelay, 15 4TapDelay, 16 RotarySpeaker, 17 Chorus-D, 18 Enhancer, 19 Edison, 20 AutoPan/Trem, 21 T-RayDelay, 22 TC-DeepVerb, 23 FlangerRev, 24 ChorusRev, 25 DelayRev, 26 ChamberRev, 27 RoomRev, 28 VintageRoom, 29 DualPitch, 30 MidasEQ, 31 FairComp, 32 MBDistortion, 33 NoiseGate, 34 DecimatorDelay, 35 VintagePitchShift (`params.json > effects`). Chaque paramètre d'effet : valeur 0..|steps|−1.

### Matrice de modulation
- **Sources** (octet `93+3k`, 0..24) : table de libellés à `0x14086f0c0` : 0 None, 1 Pitch Bend, 2 Mod Wheel, 3 Foot Ctrl, 4 BreathCtrl, 5 Pressure, 6 LFO 1, 7 LFO 2, 8 Env 1, 9 Env 2, 10 Env 3, 11 Note Num, 12 Note Vel, 13 Ctrl Seq, 14 LFO1 (uni), 15 LFO2 (uni), 16 LFO1 Fade, 17 LFO2 Fade, 18 NoteOffVel, 19 Voice Num, 20 CC X(115), 21 CC Y(116), 22 CC Z(117), 23 Uni Voice, 24 Expression. [I : ordre = ordre du tableau ; borne 24 prouvée]
- **Destinations** (octet `94+3k`, 0..132) : table de libellés à `0x14086e9b0` (`params.json > label_tables`, indices 0..132 ; getter `FUN_14043a1b0`) : 0 None, 1 LFO1 Rate … 126–129 Fx1–4 Level, 130 Osc1+2 Fine, 131 Osc1 Fine, 132 Osc2 Fine. [I : borne 132 = 133 entrées]
- **Profondeur** (octet `95+3k`) : 0..255, défaut 0x80 [I].

## 3. Ce qui n'est PAS établi
- Noms des paramètres 0..92 et 53..79 (non stockés dans le binaire, UI par images).
- Position exacte du réglage de volume maître : **aucun octet de « volume maître » identifié** dans le programme ; le volume maître est probablement un paramètre global (300..354) — à vérifier (tâche 6).
- Rôle des octets 0x21 (33) et 0x55 (85) : traités par du code spécial à la lecture (`FUN_1404050c0`, `FUN_140404b70`) ; sémantique [?].
- Un fichier `.syx` produit par l'éditeur n'a jamais été comparé à un fichier réel (pas d'échantillon) : la structure est déduite du code de lecture/écriture.

## Vérification sur le matériel (ajout)
Une partie du plan a été confirmée sur le synthé réel par écoute passive (`notes/hardware_check.md`, `notes/named_params.csv`, journal `work/midi_log.txt`) :
- **Matrice de modulation** : slots 1, 2 et 8 = octets (93,94,95), (96,97,98), (114,115,116) = `[source 0..24, destination 0..132, profondeur 0..255]` ; les slots 3..7 (99..113) suivent la même formule (déduit).
- **Enveloppes** : blocs de 9 octets, `ADSR` puis 5e octet (VCA 53..57, VCF 62..66, MOD 71..75) puis **4 courbes A/D/S/R** (VCA 58..61, VCF 67..70, MOD 76..79) [vérifié pour les courbes ; le 5e octet, borne 4, est vu une fois (75) et reste sans nom].
- **Autres zones nommées** : LFO 0..6 (LFO1) et 7..13 (LFO2, déduit), OSC 14..33, portamento/pitch 34..37 et 241, VCF 39..52 (dont 43..48 via l'écran), HPF 40/52, VCA 80..83, POLY 84..91, arpégiateur 155/157/160.
- **Globals** nommés : 325 (octave), 331 (global tune), 347 (VCA mode), 350..352 (key range, lower, upper).

**Mise à jour** : LFO 2 (octets 7..13) est maintenant **vérifié sur le matériel** (rate 7, delay 8, shape 9, key-sync 10, arp-sync 11, phase 12, slew-rate 13), identique à LFO 1 (0..6) avec un décalage de 7. La page arpégiateur (156..164), le Control Sequencer (117..122), les 12 paramètres FX du slot 2 (180..191) et les colonnes de FX OVERVIEW (166, 218..222) sont aussi vérifiés (`named_params.csv`).
