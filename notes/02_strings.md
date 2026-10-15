# Tâche 2 — Chaînes (SysEx, NRPN, paramètres, fichiers)

Méthode : (a) `scripts/Task2_DumpStrings.java` (chaînes *définies* par Ghidra : 4 483, avec xrefs -> `work/strings.tsv`) ;
(b) `scripts/strings_raw.py` (scan brut ASCII/UTF-16 de l'exe, 437 k candidats dont l'essentiel est du bruit issu du blob comprimé -> `work/strings_raw.tsv`).
Les adresses ci-dessous sont des **VA de chaînes** (ImageBase 0x140000000). Les fonctions qui les utilisent ne sont pas encore résolues : *unverified* jusqu'aux tâches 3/4.
Les chaînes utiles sont concentrées dans `.rdata` : 0x140510000–0x14052afff, 0x14086d500–0x14086e900, 0x141c0b000–0x141c2dfff. La zone ~0x140600000–0x141bfffff est du blob binaire (entropie ~7,99).

## Sources et architecture applicative (confirmé par chemins `__FILE__` embarqués)
`...\Deepmind12\BE P0AC5 APP\Source\` : `Phat12Synth.cpp` (0x14051b5c0), `Models\Presets.cpp` (0x14051ced0), `Models\PresetBlender.cpp` (0x14052a150), `Models\FirmwareUpdateThread.cpp` (0x141c0cb90), `Tabs\PresetManager\PresetManagerComponent.cpp` (0x14052a850).
Classes RTTI (0x141cc3058…) : `PresetBank`, `FlashPresetBank`, `LocalPresetBank`. Nom interne du synthé : **Phat12** (`Phat12Synth`). Un "DeepMind6" existe aussi (0x140521650, `DeepMind6Logo.png`).

## SysEx : noms de commandes (confirmé comme chaînes ; **valeurs numériques des octets inconnues** pour l'instant)
Deux familles : sans préfixe (0x140527758–0x140527ba8) et `sysexCmd*` (0x140527898–0x140527c88).
- Edit buffer / programmes : `EditBufferDumpRequest` (0x1405277a0), `EditBufferDumpResponse` (0x140527758), `ProgramDumpRequest` (0x140527788), `ProgramDumpResponse: bank = , program = ` (0x140527ba8), `ProgramNameRequest/Response` (0x140527828/0x1405277e0), `ProgramNamesRequest/Response` (0x140527850/0x140527810), `BankDumpRequest` (0x140527840).
- `sysexCmd*` : `LCDScreenDump{Request,Response}`, `CalResultsDump*`, `CalDataDump*`, `PolyChordMemDump*`, `ChordMemDump*`, `RemoteCalStatus*`, `RemoteCalOperation`, `ButtonChangeDumpResponse`, `GetDeviceUuid{Request,Response}`, `HWStatusRequest`, `FirmwareGetVersion{Request,Response}`, `WifiConfigDumpResponse`, `Category{Request,Response}`, `GetCategoryStr{Request,Response}`, `SetCategoryStrRequest`, `FavoritesMemDump{Request,Response}`.
- Firmware : `FirmwareUpgradeRequest/Response` (0x1405277f8/0x140527958) ; erreur `Unexpected incoming sysex message 0x%02x while transferring DFU` (0x141c0cf80) ⇒ l'octet de commande est affiché sur 2 chiffres hex (déduction du format, *pas* une preuve de la position).
- `AppNotifyResponse` : handler `Phat12Synth::handleAppNotifyResponse` (0x14051c528).
- Handlers nommés par chaînes de log : `handleProgramDumpResponse`, `handleEditBufferDump`, `handleBankProgramNamesResponse`, `handleProgramCategoryResponse`, `getFlashPresetData`, `getAllFlashPresetNamesForBank`, `handleIncomingNRPN`, `addressOfParameter`, `updateEditPattern`, `updateListenerWithLocalData`.
- Logs : `Requesting preset data for bank = %d, program = %d` (0x14051ca78), `Requesting all preset names for bank = %d` (0x14051cb08), timeouts `Program dump fetch timed out for bank=%d, program=%d` (0x141c14768).

## NRPN (chaînes confirmées)
`Invalid value 0x%x received for NRPN %d` (0x14051be58), `Trying to access NRPN out of scope - %d` (0x14051bee0), `Setting NRPN %d to %d` (0x14051bf08), `Receiving out of scope NRPN - param:%d, value:%d` (0x14051c948), `Binding/Unbinding NRPN %d to callback` (0x140527538/0x140527338), `Phat12Synth::addParameterListener` (0x14051bcb8).
⇒ paramètres adressés par numéro NRPN avec contrôle « out of scope » et contrôle de valeur : point d'entrée des tâches 3 et 6 (*plages non vérifiées*).
`Arp clock value is larger than expected.  Value will be clamped` (0x14051c740) : premier clamp identifié (tâche 6).

## CC / MIDI générique
`Volume (coarse)`, `Bank Select (fine)`, `Effect Control 1`, noms d'instruments GM, canaux Ambisonic… (0x140528400–0x14052a0ff) = tables **de JUCE** (`MidiMessage::getControllerName`, etc.), pas une table spécifique DeepMind. À ne pas utiliser comme table de paramètres.

## Libellés spécifiques DeepMind (0x14086d6f0–0x14086e890, pas de 16 octets)
- **Sources de modulation** : `LFO1 (uni)`, `LFO2 (uni)`, `LFO1/2 Fade|Rate|Delay|Slew|Shape`, `Note Vel`, `Ctrl Seq`, `NoteOffVel`, `Voice Num`, `BreathCtrl`, `Pressure`, `Note Num`, `CC X(115)`, `CC Y(116)`, `CC Z(117)`, `Uni Voice`, `Expression`, `Pitch Bend`, `Mod Wheel`, `Foot Ctrl`.
- **Destinations** : `OSC1 Pitch`, `OSC2 Pitch`, `OSC1+2 Pit`, `OSC1/2 PM Dep`, `PWM Depth`, `TMod Depth`, `Porta time`, `VCF Freq`, `VCF Res`, `VCF Env`, `VCF LFO`, `HP Freq`, `VCA All`, `VCA Active`, `VCA EnvDep`, `VCA Pan`, `Pan Spread`, `Env1/2/3 Attack|Decay|Sus|Rel|Rates|Curves|AtCur|DcyCur|SusCur|RelCur`, `All Attack/Decay/Sus/Rel`, `Mod 1..8 Dep`, `OSC2 Lvl`, `Noise Lvl`, `Uni Detune`, `OSC Drift`, `Param Drift`, `Drift Rate`, `Arp Gate`, `Seq Slew`, `Osc1 Fine`, `Osc2 Fine`, `Osc1+2 Fine`, **`Fx 1..4 Param1..12`**, **`Fx 1..4 Level`**.
  (Que ce soit la matrice de mod = *hypothèse forte, non vérifiée* : à confirmer par xrefs.)
- Modes : `Unison-2/3/4/6/12`, `Pass-thru`, `Norm-Open`, `Sostenuto`, `One-shot`, `Fingered`, `Fix-Rate`, `Fixed±12/24`, `Fix-Fing`, `Exp-Fing`. Arp : `UP-INV`, `UP-ALT`, `UP-DOWN`, `DOWN`, `DOWN-INV`, `DOWN-ALT`, `UP-DN-INV`, `RAND`, `AS-PLAYED`, `MANUAL`, `CHORD`, `P-Chord`. Durées : `1/12 1/16 1/24 1/32 1/48 1/64 3/16 3/32 3/64`. Formes LFO : `Triangle`, `Ramp Down`, `Smp&Hold`, `Smp&Glide`, `Square`. Filtre : `2-POLE` / `4-POLE`.
- **32 types d'effets** (0x14086e300–0x14086e520) : RichPltRev, AmbVerb, GatedRev, ReverseRev, RackAmp, MoodFilter, HallRev, PlateRev, EdisonEX1, Auto Pan, T-RayDelay, TC-DeepVRB, FlangVerb, ChorusVerb, DelayVerb, ChamberRev, Flanger, ModDlyRev, 3TapDelay, 4TapDelay, RotarySpkr, Chorus-D, Enhancer, VintgPitch, RoomRev, VintageRev, DualPitch, MidasEQ, FairComp, MulBndDist, NoiseGate, DecimDelay. Leurs paramètres nommés avec chaînes de format (`%.0f`, `%.0kf`, `%+.0f`…) sont à 0x140520000–0x140521700 (`Feedback`, `Decay`, `PreDelay`, `LoCut`, `HiCut`, `Drive`, `OutGain`, `Gain`…) : **candidat pour la table de la tâche 3**.
- **Catégories** : `NONE BASS PAD LEAD MODULAR USER-1..4 MONO POLY STAB SFX ARP SEQ PERC AMBIENT` (0x14086e4a0–0x14086e590).
- Chaînes de test usine (`VcfTimeout`, `OscOutputTooHigh`, `VcaNoiseFloorError`, `SPI Test Failed`…, 0x14086e5d8–0x14086e888) liées aux sysex `Cal*` / `HWStatus` ; **ne jamais envoyer ces commandes** (calibrage matériel).

## Banques / presets / fichiers
- Banques flash : `Synth Bank A` … `Synth Bank H` (0x14051cbf8–0x14051ce48) ⇒ 8 banques (*inférence*). Banques locales : classe `LocalPresetBank`, stockées en fichiers **`.syx`** (`.syx` @0x14051c894 et 0x14052a8f4 ; erreurs `Failed to create/copy an syx file for LocalPresetBank '%s'`).
- Contrôles à la lecture : `LocalPresetBank file is of an unusual size %db (should be %db)` (0x141c15978) et `Invalid program number in sysex file` (0x141c159b8), dans `LocalPresetBank::readFile` (lambda, 0x141c159e0) ⇒ un fichier banque = taille fixe, suite de messages SysEx (à documenter en tâche 5).
- `UserDefaults.json` (0x14052a228) : préférences de l'appli, pas les patchs.
- `We don't currently support exporting Presets` (0x14052aa40) ; `PresetBlender` : mélange de presets par timer.
- Aucun autre format (.mid/.fxp/.dm12…) trouvé : les hits du grep `*.` sont du bruit binaire.

## Réseau (hors périmètre, notable)
`https://api.cloud.music-group.com/api/v1/` (0x141c0c838), `firmware/`, `firmware/notify`, `CheckLatestFirmwareThread`, `WifiConfigDumpResponse`, champ IP « Must match IP address of DeepMind synth » (0x140936878) ⇒ transport Wi-Fi en plus du MIDI (*unverified*).
