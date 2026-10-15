# Tâche 1 — Setup et type de binaire

## Environnement (confirmé)
- Ghidra 12.1.4 PUBLIC (`application.version`), exige Java >= 21, pas de max.
- Java sur le PATH : Temurin 25.0.4.1 ; `JAVA_HOME` = Corretto 21.0.1. Les deux sont acceptables ; on force Corretto 21 dans `scripts/run_headless.ps1`.
- Python 3.14.4 présent (supporté par Ghidra 12.1.4). `pyghidra` NON installé (le module PyGhidra de Ghidra est présent mais pas pip-installé). On utilise donc des scripts **Java** (GhidraScript) via `analyzeHeadless`, sans dépendance.

## Commandes
Import du .gzf (fait, dans une copie) :
`analyzeHeadless.bat work\ghidra_proj DM12 -import work\DeepMind12.gzf -noanalysis -postScript Task1_ProgramInfo.java`
Ensuite, pour chaque script : `.\scripts\run_headless.ps1 <Script.java>` (`-process -noanalysis -readOnly`).
Piège : chemin avec espaces -> lancer depuis PowerShell (pas Git Bash).

## Type de binaire
| Élément | Valeur | Preuve |
|---|---|---|
| Format | PE32+ x86-64 (`x86:LE:64:default`, cspec windows), ImageBase `0x140000000`, EP RVA `0x25e8d8` | en-têtes PE (`scripts/pe_info.py`) + Ghidra |
| Compilateur | MSVC, linker 14.32 (VS 2022), build 2023-08-24 | en-tête optionnel PE ; Ghidra: `Compiler=visualstudio` |
| Framework | **JUCE v6.1.5** (C++) | chaînes `JUCE v6.1.5` @0x518800 (offset fichier 0x518800), `JUCE Message Thread`, `juce.com`, `juceAppLock_` |
| Classes applicatives | ex. `Phat12Synth::midiInterfaceTypeString`, `Phat12Synth::midiInputDevicesChanged` (offset fichier 0x519ea8…) | chaînes |
| MIDI | API Windows WinMM (`midiInOpen`, `midiInMessage`…), imports WINMM.dll | table d'imports |
| Packé/protégé ? | **Non** (pas de UPX/Themida/VMProtect, import table normale, `.text` entropie 5.77, 12 DLL importées) | analyse sections |
| RTTI / PDB | RTTI trouvée ; chemin PDB `DeepMind12.pdb` (pas de PDB fourni, symboles seulement RTTI/exports) | options du programme dans le .gzf |
| .NET | Non | pas d'import mscoree |

## Le .gzf
Chargé OK (loader « GZF Input Format ») : 52 823 fonctions (2 145 nommées, 50 316 `FUN_`), 194 594 symboles, 1 614 types, déjà **analysé** (`Analyzed=true`). SHA-256 du programme = celui de `DeepMind12.exe` (`f467b984…9a01c3`) : le .gzf correspond bien à cet exe.
Blocs : .text 0x4d5400, **.rdata 0x17e9a00 (~25 Mo)**, .data, .pdata, .rsrc, .reloc.

## Points d'attention / incertain
- **.rdata ≈ 25 Mo à entropie 7,8–7,99** : données comprimées/chiffrées embarquées (probablement BinaryData JUCE : images, polices, peut-être presets d'usine). *Unverified* — à examiner, peut contenir des patchs.
- `DeepMind12.bytes` (31 453 032 o, commence par `MZ`) n'est **pas identique** à l'exe (31 349 248 o, 1re différence à l'offset 30 273 538). Origine inconnue (*unverified*) ; non utilisé.
- Fichiers de travail : copies dans `work/`. Originaux non modifiés.
