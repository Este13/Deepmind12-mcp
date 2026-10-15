# Tâche 6 — Limites, clamps et risques de niveau de sortie

**[P]** = prouvé (code, adresse) ; **[I]** = inféré ; **[R]** = recommandation de ma part pour le futur MCP (pas une trouvaille).

## 1. Ce que l'éditeur vérifie réellement

| Où | Vérification | Preuve |
|---|---|---|
| **Envoi d'un paramètre** (UI → NRPN) | Le slider/contrôle clampe à `[min,max]` de son modèle (`FUN_140212050`) ; plage par défaut **0..255** (`Phat12Slider`, `FUN_14043ef70`). L'envoi écrit `(uint8)value` dans le miroir puis émet CC38 = `value & 0x7F`, CC6 = 0. **Aucune autre borne** dans `setParameter` (`FUN_14035ba80`). | [P] |
| **Envoi d'un programme** (SysEx cmd 2/4, `FUN_1404097a0`, `FUN_140408b20`) | Seule conversion : octets 36/37 → signé v−24 clampé ±24 (`FUN_140404fe0`). **Aucune borne sur les autres octets à l'émission**, y compris pour l'upload en flash (`FUN_140366fe0`). | [P] |
| **Réception d'un programme** (dump synthé ou fichier `.syx`) | `FUN_140406000` : 72 octets bornés (`params.json > value_limits_on_receive`) ; valeur > max ⇒ **remplacée par la valeur par défaut** (pas écrêtée). Octets 36/37 : `clamp(signé+24, 0, 48)` (`FUN_140405bd0`). Octet 0x55 : `FUN_140404b70`. Arp clock (158) > 12 ⇒ 12 + renvoi NRPN (`FUN_140359330`). | [P] |
| **Réception globals** (55 octets, NRPN 300..354) | `FUN_1404060c0` : borne + repli par défaut (`params.json > globals_limits_on_receive`). | [P] |
| **Réception pattern** (65 octets, NRPN 891..955) | `FUN_140405ef0` : octet 0 ≤ 31, octets 1..32 ≤ 127, octets 33..64 ≤ 128 (clamp). | [P] |
| **Réception NRPN** (`FUN_140357370`) | NRPN hors table (`FUN_14035bf30`) ignoré ; valeur 14 bits **tronquée en octet, sans borne**. | [P] |
| **Lecture d'un fichier `.syx`** | Taille = N×291 exigée ; puis même sanitisation qu'une réception (borne 72 octets). Numéro de programme > 127 : simple log. | [P] |

⇒ Les 72 + 55 + 3 bornes ci-dessus sont les **seules bornes présentes dans l'éditeur** ; les autres octets du programme (≈170 sur 242) ne sont bornés que par l'intervalle 0..255 d'un octet. **Le véritable filet de sécurité (s'il existe) est dans le firmware, non analysable ici.**

## 2. Volume maître, résonance, niveaux FX
- **Volume maître** : **aucun paramètre « volume/master » dans le programme (0..241) ni dans les globals (300..354)** ; aucune commande SysEx de volume dans la table (§ `sysex.md`) ; les libellés « Volume » du binaire sont les noms de CC de JUCE (0x1405295e4, sans rapport). Absence de preuve, pas preuve d'absence : le volume maître semble **matériel (potentiomètre)** et hors de portée de l'éditeur. [P pour l'absence dans l'éditeur, I pour la conclusion]
- **Résonance du VCF** : aucun nom d'octet dans le binaire ; le VCF est dans les octets 39, 41..49 (VCFSection, tous **sans borne** sauf 46 ≤ 1, boutons 50/51 ≤ 1). Hypothèse [I] : 39 = cutoff (défaut 0xFF = ouvert), 41 = résonance (défaut 0). **Non vérifié** ; aucune limite de résonance dans l'éditeur (0..255).
- **Niveaux FX** : octets **218..221 (FX1..4 level), max 150, défaut 0 / 100 / 100 / 100** [P bornes, I rôle]. 100 semble être « 100 % » et 150 « +50 % » (échelle non prouvée). Ils sont aussi **destinations de modulation** (dest 126..129 « Fx N Level ») : une profondeur de modulation peut donc les pousser au maximum. [I]
- **Types d'effets** (166/179/192/205) ≤ 35 ; routage FX (165) ≤ 9, 222 ≤ 2. [P]

## 3. Paramètres pouvant produire de forts niveaux ou de l'auto-oscillation (d'après les descripteurs d'effets prouvés, `params.json > effects`)
Valeurs physiques = interpolation min..max sur `|steps|` pas (octet = 0..|steps|−1).
| Effet (id) | Paramètre | Plage physique | Risque |
|---|---|---|---|
| MBDistortion (32) | InGain / OutGain | −24..+24 dB / −12..+12 dB | jusqu'à +36 dB cumulés + distorsion |
| Enhancer (18) | OutGain | −12..+12 dB | +12 dB |
| Edison EX1 (19) | Gain | −12..+12 dB | +12 dB |
| FairComp (31) | InGain L/M, R/S ; OutGain L/M, R/S | −20..+10 dB ; −18..+6 dB | +16 dB cumulés par canal |
| MidasEQ (30) | Lo/LoMid/HiMid/HiShelf gain | ±16 dB | +16 dB par bande (bandes cumulables) |
| Delay/echo (4 effets) | Feedback | 0..100 % | auto-oscillation/accumulation à 100 % |
| FlangerRev (23) | Feedback | −90..+90 % | forte résonance |
| Mood Filter (8) / autres | Reso | 0..100 % (une à 0..80) | résonance/auto-oscillation |
| Rack Amp (7), autres | PreAmp / Drive / Level | 0..10 ou 0..100 | saturation, gain |
| Reverbs | Decay, Size (jusqu'à 76, 100) ; Mix | — | queues très longues (énergie cumulée) |
| Fx level (218..221) | niveau | 0..150 | > 100 % |

Côté synthé (bornes [P] sur octets, rôle [I]) : polyphonie/unison (**Unison-12** = 12 voix superposées, cf. libellés `Unison-2/3/4/6/12`), profondeurs de modulation (octets `95+3k`, 0..255 non bornées) vers destinations « VCF Res », « VCA All », « Fx N Level » (dest 126..129 [P libellés]).

## 4. Points de vigilance pour un serveur MCP [R]
1. **Ne pas s'appuyer sur l'éditeur pour valider** : il n'écrête pas à l'envoi. Le MCP doit imposer lui-même : bornes des 72+55+3 octets ci-dessus ; bornes des paramètres d'effet `0..|steps|−1` ; octets 36/37 dans 0..48 ; nom = 16 octets ASCII 0x20..0x7E + padding.
2. **Écrire dans le buffer d'édition (cmd 4), pas en flash (cmd 2)** ; ne jamais réutiliser `FUN_140366fe0`-like (écrasement de presets sur 200 ms/programme). Demander une confirmation avant toute écriture en flash.
3. **NRPN : l'éditeur n'envoie que 0..127** (mais le matériel émet du 14 bits, cf. `hardware_check.md`, donc préférer CC6 = v>>7) (CC6=0, CC38 = `v & 0x7F`) : envoyer 128..255 par NRPN **repasse à valeur−128** (129 → 1). Pour un octet > 127 passer par SysEx edit-buffer. [P sur le code de l'éditeur ; comportement du firmware non vérifié]
4. **Plafonner par défaut** : FX level ≤ 100, gains d'effets ≤ 0 dB (octet = valeur défaut), feedback ≤ ~70 %, résonance ≤ ~80 %, pas de modulation Fx Level/VCA All avec grande profondeur sans confirmation ; **ne pas générer de patch dont le niveau ne peut pas être borné** ; toujours partir de « Default Program ».
5. **Interdire** : SysEx 0x11–0x1A (calibrage/écran/boutons), 0x71–0x72 (firmware/DFU), 0x1F (config Wi-Fi), 0x26 (SetCategoryStr) sauf besoin explicite ; ne pas utiliser l'envoi de dumps de type Favorites/Chord sans les comprendre.
6. Toute valeur d'un programme reçu > borne est remplacée par la valeur par défaut : un round-trip lecture → écriture peut donc **modifier silencieusement** des octets hors bornes (réglages de banques importées).

## 5. Incertain / non fait
- Tous les rôles d'octets non nommés (résonance, volume de sortie de VCA, etc.) ; le firmware peut borner différemment, ou pas du tout.
- Échelle réelle du niveau FX (0..150) et du gain de sortie en dB.
- Effet concret de l'octet 0x55 et 0x21 (traitements spéciaux à la lecture).
- Aucune vérification matérielle (interdite par les règles du projet).

## Décision de périmètre (utilisateur, 2026-09-28)
**Le bloc Globals (NRPN 300..354, SysEx cmd 5/6) est exclu du MCP** : aucune lecture-écriture de ces octets (menu GLOBAL : canaux MIDI, device id, horloge, interface, VCA-MODE, tune global, key range, octave…). Le MCP ne doit écrire que dans le programme (octets 0..241) et jamais dans les globals. Les octets globaux observés restent documentés (`named_params.csv`) à titre d'information uniquement.

## Écriture vérifiée (ajout)
Écritures de programme dans l'**edit buffer** validées sur le matériel (voir `hardware_check.md`, section « Tests d'écriture »). Règles retenues pour le MCP : édition du programme (octets 0..241) **uniquement** via SysEx edit-buffer (cmd 4, version 7, device id lu depuis l'Identity) ; lecture/sauvegarde avant toute écriture ; validation systématique ; jamais de flash (cmd 2), jamais de Globals (cmd 5/6, NRPN 300..354), jamais de firmware/calibrage.
