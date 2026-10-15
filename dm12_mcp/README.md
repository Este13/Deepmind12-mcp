# Serveur MCP DeepMind 12 (presets avec garde-fous)

Permet à une IA de **créer et modifier le patch courant** d'un Behringer DeepMind 12 branché en USB, en écrivant uniquement dans le **buffer d'édition (volatil)**.

## Ce qu'il fait / ne fait pas
- Lit le patch courant, le décode (nom, paramètres, effets en unités physiques, matrice de modulation).
- Simule des changements (aucun envoi), les valide, puis les écrit dans l'edit buffer, relit et compare. L'état précédent est sauvegardé (`work/backups/`) et restaurable.
- **Ne touche jamais** : flash / banques A–H (pas de cmd 2), **Globals** (menu GLOBAL, NRPN 300..354), firmware/DFU, calibrage, Wi-Fi/réseau. Ces trames sont refusées dans le code (`scripts/midi_safe.py`, `scripts/midi_dm12.py`).
- Pour enregistrer un preset définitivement, l'utilisateur appuie lui-même sur WRITE sur le synthé.

## Installation
```
pip install mcp          # SDK 2.x (testé avec 2.2.0)
```
Windows uniquement (WinMM). Le synthé doit apparaître comme entrée+sortie MIDI « DeepMind12 » (index 0 en entrée, 1 en sortie ; voir `scripts/midi_list.py`).

## Déclaration (exemple `.mcp.json`)
```json
{
  "mcpServers": {
    "deepmind12": {
      "command": "python",
      "args": ["dm12_mcp/server.py"]
    }
  }
}
```
Vérification rapide sans client : `python scripts/mcp_smoke_test.py` (lit, simule, écrit un changement neutre puis restaure).

## Outils
| Outil | Rôle |
|---|---|
| `dm12_status` | Identity Request (lecture seule) et périmètre |
| `dm12_read_patch` | Patch courant décodé |
| `dm12_list_parameters(section)` | Paramètres pilotables (clé, max, défaut, niveau de preuve) |
| `dm12_list_effects(effect)` | 35 effets et leurs paramètres (plages physiques, log/lin) |
| `dm12_list_modulation` | Sources (25) et destinations (133) de la matrice |
| `dm12_preview_changes` | Simulation sans envoi |
| `dm12_apply_changes` | Écriture edit buffer : `dry_run=false` **et** `confirm="EDIT_BUFFER_ONLY"` |
| `dm12_list_backups` / `dm12_restore_backup` | Sauvegardes avant écriture / restauration |

Clés de `changes` : `vcf.cutoff`, `osc1.saw_on`, `env_vca.attack`, `arp.rate`… (voir `dm12_list_parameters`), `name`, `fxN.type` (nom ou id), `fxN.<Paramètre>` (unité physique), `modN.source|dest|depth` (noms acceptés).

## Sécurité
- Bornes prouvées (binaire de l'éditeur) refusées en dur ; noms de 16 caractères ASCII.
- Seuils « risqués » bloqués sauf `allow_risky=true` : résonance > 220, niveau FX > 100, gain d'effet > 0 dB, feedback > 70 %, reso/drive d'effet élevés.
- Octets inconnus (57, 66, 75, 123..154, 239..241…) **conservés** à l'identique.
- Baisser le volume du synthé avant de tester un patch généré.

## Limites connues
- Ordre des libellés d'enums non vérifié pour tous les index (formes de LFO, modes d'arpégiateur, sources/destinations de la matrice) : utiliser les index si un nom est ambigu.
- Pas d'export de fichiers `.syx` de banque (format déduit, non comparé à un fichier réel).
- Testé sur le firmware 1.1.2-619 uniquement.
- Ne gère pas le device id ≠ 0 (le synthé testé répond avec l'id 0).
