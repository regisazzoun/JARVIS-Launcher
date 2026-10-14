#!/bin/bash
set -euo pipefail
if [ "$(uname -s)" != Darwin ]; then printf '%s\n' 'Test natif uniquement sur macOS.' >&2; exit 1; fi
project_root=$(cd -- "$(dirname "$0")/.." && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/jarvis-launcher-smoke.XXXXXX")
trap 'rm -rf -- "$temporary_dir"' EXIT
/usr/bin/osacompile -o "$temporary_dir/Launcher.app" "$project_root/macos/Launcher.applescript"
for script in launcher setup hardware; do
  /usr/bin/osacompile -l JavaScript -o "$temporary_dir/$script.scpt" "$project_root/macos/$script.js"
done
/usr/bin/osascript -l JavaScript "$project_root/tests/native-core.js" "$project_root"
printf '%s\n' 'Compilation et politique seules validées. Réception réelle sur chaque Mac encore nécessaire.'
