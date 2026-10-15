d="$(cd "$(dirname "$0")/.." && pwd -W)"
powershell -NoProfile -File "$d/scripts/run_headless.ps1" "$@" > "$d/work/last_run.txt" 2>&1
grep -a -E "\.java>|ERROR|Exception" "$d/work/last_run.txt" | sed 's/.*\.java> //' | cut -c1-${WIDTH:-220}
