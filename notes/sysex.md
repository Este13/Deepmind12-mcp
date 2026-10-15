# Tâche 4 — SysEx (analyse statique)

Toutes les adresses sont des VA dans `DeepMind12.exe` (ImageBase 0x140000000). « Prouvé » = lu dans le code décompilé ; « inféré » / « unverified » sinon. Scripts : `XrefDecompile.java`, `DecompRange.java`, `Callers.java` (dans `scripts/`).

## 1. Trame et en-tête (prouvé)
Message DeepMind (constructeurs `FUN_1401ec5a0/680/760/7c0/840/920/9a0/a20/b00/ca0/cd40`, en-tête = 5 octets constants `F0 00 20 32 20` lus à `0x141c2aac0`) :

| idx | valeur |
|---|---|
| 0 | `F0` |
| 1..3 | `00 20 32` = ID fabricant (Behringer) |
| 4 | `20` = famille/modèle (DeepMind 12 ; confirmé en réception par la réponse Identity, §2) |
| 5 | **device id** (octet, voir §2) |
| 6 | **commande** (`FUN_140409b00` lit `msg[6]`) |
| 7… | arguments / charge utile (selon commande) |
| dernier | `F7` |

Réception : `Phat12Synth::handleMessage` (`FUN_140359bc0` @0x140359bc0) : si `msg[0]==F0` et `msg[1]==7E` → Identity reply (§2), sinon dispatch `switch(msg[6]-2)` (tableau §3). **Aucun filtrage** sur ID fabricant/device id dans ce dispatcher (inféré : pas de test vu, à confirmer).
Envoi : `Phat12Synth::send` (`FUN_14035c280` @0x14035c280) ; le message n'est envoyé que si l'état de connexion ≠ 0 (`synth+0x1860`) ; sinon jeté silencieusement.

## 2. Handshake (prouvé)
1. **Device Inquiry** (`FUN_14040a770` @0x14040a770) : `F0 7E <dev> 06 01 F7` (Identity Request universel, `dev` = octet passé).
2. **Réponse** attendue (tests dans `FUN_140359bc0`) : `F0 7E <dev> 06 02 00 20 32 20 00 01 00 <ver…> F7` : `msg[3]==6`, `msg[4]==2`, `msg[8]==0x20`, `msg[9]==0`, `msg[10]==1`, `msg[11]==0` (famille `20 00`, membre `01 00`). Sinon log « Handshake failed » et état=0. Le device id de la réponse (`msg[2]`) est stocké dans l'**NRPN 302** (`FUN_14035c720` → `setParameter(302)`), puis le log affiche « Discovered PHAT12 %d v%d.%d (voice %d.%d) » avec `msg[12]>>4 . msg[12]&0xF` et `msg[14]`, `msg[15]` (rôle exact des champs version : inféré).
3. **AppNotify** (`FUN_14040a7f0` @0x14040a7f0) : `F0 00 20 32 20 <dev> 00 F7` (cmd 0). La synthé répond `AppNotifyResponse` (cmd 0x10, `FUN_1403594c0` @0x1403594c0) : `msg[5]`=device id, `msg[8]`=canal RX, `msg[9]`=canal TX, `msg[10]`=type d'interface (0/1/3 => 3 libellés), `msg[11]`, `msg[12]` mémorisés (`synth+0x1864/0x1865`, « Comms Protocol » : inféré). Log : « Connectedto to PHAT12 via %s. Rx:%d, Tx:%d, DeviceID:%d, Comms Protocol:%d ».

## 3. Table des commandes (prouvée : `FUN_140408c50` @0x140408c50, switch sur `msg[6]`)
| cmd | nom | remarques |
|---|---|---|
| 0x00 | AppNotify | app -> synthé |
| 0x01 | ProgramDumpRequest | `hdr dev 01 bank prog F7` (10 o., `FUN_14040a260`) |
| 0x02 | ProgramDumpResponse | 291 o. (voir §4) — handler `FUN_140358fe0` |
| 0x03 | EditBufferDumpRequest | `hdr dev 03 F7` (8 o., `FUN_14040a670`) |
| 0x04 | EditBufferDumpResponse | 289 o. — handler `FUN_140359330` |
| 0x05 | GlobalsDumpRequest | 8 o. (`FUN_14040a6f0`) |
| 0x06 | GlobalsDumpResponse | 0x37=55 octets dépackés (`FUN_140359450`) = NRPN 300..354 |
| 0x07 | UserPatternDumpRequest | |
| 0x08 | UserPatternDumpResponse | 90 o. : `hdr dev 08 07 <n° pattern> [80 o. packés de 65] F7` (`FUN_14040a4b0`) |
| 0x09 | BankDumpRequest | `hdr dev 09 bank 00 7F F7` (11 o., `FUN_14040a330` : programmes 0..127) |
| 0x0A | ProgramNamesRequest | `hdr dev 0A bank F7` (9 o., `FUN_14040a0b0`) |
| 0x0B | ProgramNamesResponse | `msg[8]`=bank (<8), payload `msg+9` : 0x928 o. packés -> 2048 o. = 128 noms × 16 (`FUN_140358b40`) |
| 0x0C / 0x0D | ProgramNameRequest / Response | noms présents dans la table, mais **aucun handler** dans le dispatch de réception (cmd 0xD tombe en « Unhandled message ») |
| 0x0E | EditPatternDumpRequest | 9 o. (`FUN_14040a400`) |
| 0x0F | EditPatternDumpResponse | 0x41=65 octets = NRPN 891..955 (`FUN_140358a90`) |
| 0x10 | AppNotifyResponse | §2 |
| 0x11–0x1A | sysexCmd Cal*/RemoteCal*/LCDScreen/ButtonChange | **calibrage / debug matériel**, jamais à exposer |
| 0x1B–0x1E | ChordMem / PolyChordMem Dump Req/Resp | |
| 0x1F | WifiConfigDumpResponse | |
| 0x20, 0x21 | HWStatusRequest (les deux libellés identiques dans le binaire) | |
| 0x22 / 0x23 | FavoritesMemDump Request / Response | 128 octets (`FUN_140358830`) |
| 0x24 / 0x25 | GetCategoryStr Request / Response | 32 octets (`FUN_1403588e0`) |
| 0x26 | SetCategoryStrRequest | 48 o. : payload 0x20 (`FUN_140409e60`) |
| 0x27 / 0x28 | CategoryRequest / CategoryResponse | `hdr dev 27 bank F7` ; réponse : `msg[8]`=bank, `msg[9..]` 0x98 packés -> 128 octets (1 catégorie/programme, `FUN_140358470`) |
| 0x71 / 0x72 | FirmwareUpgradeRequest / Response | **mise à jour firmware/DFU : ne jamais envoyer** |
| 0x73 / 0x74 | FirmwareGetVersionRequest / Response | réponse 6 octets |
| 0x75 / 0x76 | GetDeviceUuidRequest / Response | réponse 48 octets |

Dispatch de réception prouvé : cmd 2→`140358fe0`, 4→`140359330`, 6→`140359450`, 8→`140358b10` (vide), 0xB→`140358b40`, 0xF→`140358a90`, 0x10→`1403594c0`, 0x23→`140358830`, 0x25→`1403588e0`, 0x28→`140358470`, 0x72→erreur « FirmwareUpgradeResponse during normal operation », 0x74→`140358980`, 0x76→`1403589c0`. Les autres cmd tombent en « Unhandled message ».

## 4. Programme / Edit buffer (prouvé)
**ProgramDumpResponse (cmd 2)**, construit par `FUN_1404097a0` (@0x1404097a0) : 291 octets :
`F0 00 20 32 20 <dev> 02 <07> <bank> <prog> <280 octets> F7`
**EditBufferDumpResponse (cmd 4)**, `FUN_140408b20` : 289 octets : `F0 00 20 32 20 <dev> 04 <07> <280 octets> F7`.
- `<07>` (idx 7) = **numéro de version de format** ; l'éditeur envoie 7. En réception `FUN_140405e10/e80` acceptent 1..7 (même longueur attendue : 291 / 289, sinon le message est rejeté : `FUN_140405cb0` renvoie faux) ; les versions < 6 sont migrées par `FUN_140405770` (fonctions 0x1404050c0…0x1404056a0).
- `bank` doit être < 8, `prog` < 0x80, sinon « Invalid ProgramDumpResponse » (0x140358fe0).
- Charge utile : programme de **242 octets** (voir `patch_format.md`) **packé 7 bits** :
  **pack** (`FUN_140404d40` @0x140404d40) : par groupe de 7 octets source `b0..b6` → 8 octets : `out0 = Σ (b_j >> 7) << j` (bit j = MSB de l'octet j, j=0..6) ; `out1..7 = b_j & 0x7F`. Padding de zéros. 242 → 35 groupes → **280 octets**.
  **unpack** (`FUN_140406130` @0x140406130) : inverse (`b_j = ((out0>>j)&1)<<7 | out_{1+j}`).
- **Pas de checksum** dans ces dumps (ni au pack, ni au unpack, ni dans le handler) : prouvé pour les cmd 2 et 4.
- Avant l'envoi : `FUN_140404fe0` (@0x140404fe0) convertit les octets 36 et 37 : `signé = clamp(v-24, -24, +24)` ; à la réception `FUN_140405bd0` fait l'inverse (`clamp(signé+24, 0, 48)`).
- Après réception : `FUN_140406000` (@0x140406000) applique la table de bornes (72 entrées, `params.json > value_limits_on_receive`) : valeur > max => remplacée par la valeur du programme par défaut ; puis l'octet 0x55 passe par `FUN_140404b70`.
- Le nom (octets 223..238, 16 caractères) est dans le programme lui-même.

## 5. Autres canaux (prouvé)
Les paramètres unitaires passent en **MIDI CC/NRPN** (pas SysEx) : voir `notes/03_params.md` §2 (`FUN_14035ba80`). Réception CC : `0xB0|canal`, CC 99/98/6/38/32 (Bank Select LSB) traités par `FUN_140359bc0`.
Réception : CC 99 → `+0x17d8`, CC 98 → `+0x17d9`, CC 6 → `+0x17da` (data MSB), CC 38 → `+0x17db` puis application immédiate (`FUN_140357370`), CC 32 → `+0x1864`. Le NRPN est donc appliqué dès le CC 38. Les CC ne sont acceptés que si `canal == RX` ou canal 0xF (omni).

## 6. Incertain / non fait
- Contenu exact des ChordMem/Favorites/Wifi/Cal* : non analysé (hors périmètre édition de presets).
- Rôle du device id à l'émission (valeur par défaut, broadcast) : `dev` provient de l'NRPN 302 (`FUN_14035c760`) ; plage non vérifiée.
- Pas de vérification que le firmware exige la même trame : à valider matériellement (interdit ici).
- Les commandes de calibrage (0x11–0x1A) et firmware (0x71–0x72) **doivent rester hors d'un futur serveur MCP**.
