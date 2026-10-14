#!/bin/bash
# Optional operator-run publication. Never merges or writes to JARVIS-Local-AI-Lab.
set -euo pipefail
project_root=$(cd -- "$(dirname "$0")/.." && pwd)
cd "$project_root"
repository=regisazzoun/JARVIS-Launcher
branch=codex/jl-01-jarvis-launcher
command -v gh >/dev/null || { printf '%s\n' 'GitHub CLI gratuit requis. Voir docs/PUBLICATION.md.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { printf '%s\n' 'Authentifiez gh avec gh auth login ; aucun jeton dans les sources.' >&2; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { printf '%s\n' 'Clonez le bundle Git fourni ; le ZIP seul ne contient pas l’historique Git.' >&2; exit 1; }
[ "$(git branch --show-current)" = "$branch" ] || { printf 'Placez-vous sur %s.\n' "$branch" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { printf '%s\n' 'Enregistrez les modifications locales avant publication.' >&2; exit 1; }
if ! git show-ref --verify --quiet refs/heads/main; then git branch main refs/remotes/origin/main; fi
[ "$(git ls-tree -r --name-only main)" = README.md ] || { printf '%s\n' 'main doit contenir seulement le README d’initialisation ; aucune publication automatique de code sur main.' >&2; exit 1; }
if gh repo view "$repository" --json isEmpty --jq '.isEmpty' > /dev/null 2>&1; then
  [ "$(gh repo view "$repository" --json isEmpty --jq '.isEmpty')" = true ] || { printf '%s\n' 'Le dépôt dédié contient déjà des données. Publication arrêtée pour les préserver. Voir la procédure de reprise dans docs/PUBLICATION.md.' >&2; exit 1; }
else
  gh repo create "$repository" --public --description 'Lanceur gratuit macOS pour les terminaux et connexions JARVIS — frontend GitHub Pages, protocole local sécurisé'
fi
remote_current=$(git config --get remote.origin.url || true)
case "$remote_current" in
  '') git remote add origin "https://github.com/$repository.git" ;;
  "https://github.com/$repository.git"|"git@github.com:$repository.git") ;;
  *.bundle) git remote set-url origin "https://github.com/$repository.git" ;;
  *) printf '%s\n' 'Remote origin inattendu ; aucune modification du dépôt distant.' >&2; exit 1 ;;
esac
git push origin main
gh repo edit "$repository" --default-branch main
git push --set-upstream origin "$branch"
gh pr create --repo "$repository" --base main --head "$branch" --title 'JL-01 : interface JARVIS Launcher et protocole macOS sécurisé' --body-file docs/PR.md
python3 scripts/build.py
pages_dir=$(mktemp -d "${TMPDIR:-/tmp}/jarvis-launcher-pages.XXXXXX")
trap 'rm -rf -- "$pages_dir"' EXIT
cp -R dist/pages/. "$pages_dir/"
git -C "$pages_dir" init -q -b gh-pages
git -C "$pages_dir" add .
git -C "$pages_dir" -c user.name='JARVIS Launcher' -c user.email='jarvis-launcher@localhost' commit -q -m 'pages: publier le site statique JL-01'
git -C "$pages_dir" remote add origin "https://github.com/$repository.git"
git -C "$pages_dir" push origin gh-pages
printf '%s\n' 'Code et PR publiés ; aucune fusion vers main.'
printf '%s\n' 'Activez Pages : Settings → Pages → Deploy from a branch → gh-pages → / (root).'
printf '%s\n' 'Ou : gh api --method POST repos/regisazzoun/JARVIS-Launcher/pages -f build_type=legacy -f "source[branch]=gh-pages" -f "source[path]=/"'
printf '%s\n' 'URL attendue après activation : https://regisazzoun.github.io/JARVIS-Launcher/ (à vérifier, pas encore validée).'
