# Vérification sur le matériel (lecture seule)

Date : session du 2026-09-28. Scripts : `scripts/midi_safe.py` (liste blanche de trames sortantes), `midi_list.py`, `midi_identity.py`, `midi_read.py`, `decode_dump.py`. Journal complet des échanges : `work/midi_log.txt`. Dumps bruts : `work/dumps/`.
Seules trames envoyées : Identity Request `F0 7E 7F 06 01 F7`, EditBufferDumpRequest `F0 00 20 32 20 00 03 F7`, GlobalsDumpRequest `F0 00 20 32 20 00 05 F7`. Rien d'autre (aucune écriture, aucun firmware/calibrage).

## Confirmé sur le matériel
| Point | Prédit (statique) | Observé |
|---|---|---|
| Port USB | — | entrée et sortie « DeepMind12 » (WinMM) |
| Réponse Identity | `msg[3..4]=06 02`, `msg[8..11]=20 00 01 00`, device id → NRPN 302 | `F0 7E 00 06 02 00 20 32 20 00 01 00 00 00 00 00 F7` (device id 0, octets version 00) |
| EditBufferDump (cmd 4) | 289 octets, version 7, `F0 00 20 32 20 dev 04 07 [280] F7` | **289 octets, `f0 00 20 32 20 00 04 07 …`** |
| Dépack 7 bits | 242 octets | OK ; aucune valeur hors des 72 bornes |
| Nom du programme | octets 223..238 | `Hitones Love GR ` (16 car., complété d'espaces ici, pas de NUL) |
| Types d'effets 166/179/192/205 | ≤ 35 | 19 (Edison), 22 (TC-DeepVerb), 0, 0 |
| GlobalsDump (cmd 6) | 55 octets dépackés, payload à `msg+8`, 73 octets au total | **73 octets** ; NRPN 302 (device id) = 0, cohérent avec la réponse Identity |

## Écarts / notes
- Le nom est complété par des **espaces (0x20)**, pas par des NUL : le padding NUL du programme par défaut n'est donc pas la règle du firmware.
- Global 339 = 2 alors que la table de bornes de l'éditeur dit max 1 (défaut 2) : **la table de bornes de l'éditeur n'est pas exacte pour cet octet** (le firmware produit une valeur que l'éditeur remplacerait par son défaut).
- Octets 36/37 du programme (décodés du fil) : `0x00 / 0x00` ici ; la conversion signée (v−24) est à vérifier avec une valeur non nulle.
- Le synthé émet spontanément des notes MIDI (clavier/arpégiateur) ; aucun NRPN observé pendant l'écoute passive de 5 s (aucun potard touché).

## Non fait
Écriture de paramètres (NRPN / edit buffer), tests de bornes, lecture des banques flash.

## Cartographie des potards par écoute passive (NRPN émis par le synthé)
Méthode : `scripts/midi_listen_ctrl.py <secondes> "<étiquette>"` (aucun envoi), l'utilisateur bouge un potard/bouton à la fois dans un ordre annoncé ; les NRPN sont identifiés par leur **ordre d'apparition**. Résultats : [`named_params.csv`](named_params.csv) (37 contrôles). Journal brut : `work/midi_log.txt`.

**Constat important sur le format NRPN émis par le firmware** : le synthé envoie `CC99 = n>>7, CC98 = n&0x7F, CC6 = v>>7, CC38 = v&0x7F` : la valeur 0..255 utilise **le MSB de données (CC6) pour le bit 7** (ex. `b0 63 00 / b0 62 07 / b0 06 01 / b0 26 51` = NRPN 7, valeur 128+0x51 = 209). Les potards vont bien de **0 à 255** (min/max observés). L'éditeur, lui, envoie toujours CC6 = 0 et CC38 = v & 0x7F (cf. `03_params.md`/`safety.md`) : **pour émettre 128..255 il faut envoyer CC6 = v>>7** comme le fait le matériel (comportement de réception du firmware non testé).

**Volume** : le potard VOLUME n'émet aucun message MIDI : réglage purement matériel (confirme tâche 6).
**Résonance VCF = NRPN 41, cutoff = 39** : plage 0..255, aucune limite logicielle observée côté synthé.
Structure vérifiée : LFO1 = octets 0/1 (rate/delay) et LFO2 = 7/8 (même schéma, +7) ; enveloppes = blocs de 9 octets (VCA 53..57, VCF 62..66, MOD 71..75) dont les 4 premiers sont A/D/S/R.

## Vérification de la table d'effets (RoomRev, slot 2) — 12/12
Dump lu en lecture seule (edit buffer) + photos LCD + écoute :
- Formule **prouvée** : octet = numéro de pas (0..|steps|−1) ; valeur physique = min + (max−min)·pas/(|steps|−1) si steps > 0 ; **min·(max/min)^(pas/(|steps|−1)) si steps < 0** (échelle log). Les 12 valeurs recalculées (PRE 0, DCY 2.95, SIZ 76, DMP 3484 Hz, DIF 100, MIX 15, LC 32.3, HC 2000 Hz, LFX 1.0, SPR 33, SHP 100, SPI 50) égalent l'affichage de l'écran ; EdisonEX1 SW = 5.0 dB (octet 34/49).
- NRPN = `167 + 13·slot + index` ; maxima observés 180..191 = 254, 50, 36, 24, 25, 100, 50, 50, 52, 50, 50, 20 = |steps|−1 de la table.
- Colonne LVL de FX OVERVIEW = octets 218..221 (slot 4 affiche 101 = octet 221 du dump).
- NRPN 222 (0..2) = réglage de la ligne du haut de FX OVERVIEW (« Insert »).

## Menu GLOBAL (photos, aucun NRPN capté ; exclu du MCP par décision de l'utilisateur)
Pages : SYSTEM SETTINGS (HOST/VOICE/DSP-VER **1.1.2-619**, BOOT-VER 23, WIFI-VER 2.7.0.0, FAN-SPEED, CALIBRATE, BACKUP), CONNECTIVITY (DEVICE-ID, MIDI/USB/WIFI/NETWORK SETTINGS, EXPORT), KEYBOARD SETTINGS, PEDAL SETTINGS, PANEL SETTINGS.
Notes utiles :
- **Firmware testé : 1.1.2-619** (éditeur analysé : build du 2023-08-24). Tout ce document décrit ce couple.
- **DEVICE-ID affiché = 1** alors que le NRPN 302 / la réponse Identity donnent 0 : l'écran affiche id+1.
- **MIDI SETTINGS** (non explorée) contient vraisemblablement le mode de réception des paramètres (NRPN/CC/SysEx) : si l'utilisateur le change, l'écriture par NRPN peut cesser de fonctionner ; le SysEx edit-buffer est la voie la plus robuste.
- ARP-PARAMS (NRPN 338, PROGRAM/GLOBAL) : en mode GLOBAL, les réglages d'arpégiateur du programme sont ignorés au profit des globaux.

## Tests d'écriture dans l'edit buffer (2026-09-28, firmware 1.1.2-619) — TOUS RÉUSSIS
Scripts : `scripts/midi_dm12.py` (pack/dépack, validation, écriture edit-buffer seule), `midi_write_test.py`, `midi_write_full_test.py`. Sauvegardes avant chaque test : `work/dumps/backup_before_*.syx`. Trame envoyée : `F0 00 20 32 20 00 04 07 <280 octets packés> F7` (device id 0, cmd 4, version 7) ; aucun envoi en flash ni sur les Globals.
1. **Pack/dépack** : la reconstruction hors ligne reproduit le dump du matériel à l'octet près (289/289).
2. **Renvoi à l'identique** : accepté, relecture identique.
3. **Modification d'un seul octet** (Portamento Time, octet 34) : seul cet octet change à la relecture.
4. **Patch complet** (construit à partir du Default Program, nom « MCP TEST », cutoff/résonance/enveloppes/LFO/matrice/FX RoomRev) : accepté, **relu identique octet pour octet**, nom conservé ; aucune valeur réécrite par le firmware.
5. **Restauration** du patch d'origine vérifiée identique après chaque test.
Conclusions : (a) le SysEx edit-buffer version 7 est la voie d'écriture fiable ; (b) le firmware accepte les octets 36/37 tels qu'il les émet (valeur 2 pour +2) : ne pas appliquer la conversion « v−24 » de l'éditeur ; (c) le format du nom est 16 caractères ASCII complétés par des espaces.
