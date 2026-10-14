# JARVIS Launcher — JL-01

Votre point de départ pour les terminaux et connexions JARVIS. Interface statique responsive, application macOS légère et gratuite, aucun backend public ni serveur HTTP local permanent. Projet indépendant de JARVIS Local AI Lab.

**GO AVEC RÉSERVES pour livraison et prétests.** Neuf tests automatisés passent, dont 67 cas de politique de sécurité. L’installation native, les deux vrais Macs et la véritable origine GitHub Pages restent à réceptionner. Dépôt GitHub dédié et site pas encore publiés : la capacité de création du dépôt n’est pas disponible dans cette session. Voir [le rapport JL-01](docs/RAPPORT-JL-01.md) et [la publication préparée](docs/PUBLICATION.md).

## Fonctionnalités

- Profils **MacBook Pro / Mac mini** : le poste depuis lequel vous travaillez, jamais deux serveurs. Sélection, session et favoris persistants dans le navigateur.
- SSH JARVIS via Tailscale ; Codex normal dans `/home/adminjarvis/JARVIS` ; Codex sous tmux avec création/reprise exacte.
- Attachement à une session existante, liste tmux, tunnel JARVIS Web, lecture de l’état des services, secours LAN choisi explicitement.
- Trois terminaux en une action après confirmation : SSH, Codex sous tmux et tunnel web.
- Sections, favoris et libellés éditables en JSON ; commande de secours sélectionnable/copiable.
- Sur mobile et hors macOS : commandes à copier, aucune promesse d’ouverture de Terminal.app.
- Disponibilité du lanceur honnêtement « non vérifiable » dans le site ; diagnostic à afficher localement sur le Mac.

## Installation sur les deux Macs

Les sources se trouvent dans l’archive `JARVIS-Launcher-JL-01.zip`. Une fois le dépôt dédié publié, vous pourrez également les cloner et choisir la branche de travail :

```bash
git clone https://github.com/regisazzoun/JARVIS-Launcher.git
cd JARVIS-Launcher
git switch codex/jl-01-jarvis-launcher
```

Prérequis clients : macOS avec Terminal.app, osacompile/osascript, SSH natif ; clé SSH déjà installée à `~/.ssh/id_ed25519_jarvis`, ou autre chemin configuré localement ; Tailscale connecté pour la route Tailscale. Aucun Python, Node, Homebrew ou compte développeur Apple nécessaire pour le lanceur macOS.

Dans le dossier extrait/cloné, exécutez **la commande correspondant au matériel réel** :

```bash
# MacBook Pro
bash macos/install.sh macbook-pro

# Mac mini client
bash macos/install.sh mac-mini
```

Le script vérifie le nom du matériel, compile l’application, la signe localement et enregistre `jarvis-launcher://`. L’application est créée dans `~/Applications/JARVIS Launcher.app`, sans sudo. Une ancienne application du même nom est conservée sous un nom de sauvegarde ; les anciens scripts V2, clés SSH et configurations SSH ne sont ni exécutés ni écrasés. La configuration existante du lanceur est conservée à la réinstallation.

Vérifiez ensuite le protocole, sur le Mac concerné :

```bash
open 'jarvis-launcher://launch/macbook-pro/check'
# ou sur le Mac mini :
open 'jarvis-launcher://launch/mac-mini/check'
```

Ce diagnostic prouve seulement que le lanceur répond localement avec le bon profil/matériel ; il ne valide pas SSH, Codex ou le tunnel. Autorisez le navigateur à ouvrir l’application. Lors de la première exécution, autorisez le contrôle de Terminal dans la demande macOS ou Réglages Système → Confidentialité et sécurité → Automatisation. Le libellé peut mentionner le lanceur ou osascript. L’application construite localement n’est pas notariée ; si macOS la bloque, ouvrez-la volontairement via Finder / Confidentialité et sécurité après revue des sources. Ne désactivez pas Gatekeeper globalement.

## Utilisation

Choisissez votre **Mac client**, puis une action. La demande est vérifiée et confirmée localement avant que Terminal.app ouvre une nouvelle fenêtre. Le profil URL doit correspondre au profil installé ET au matériel réel. Un profil ou matériel inconnu est bloqué. La page ne peut pas détecter quel modèle de Mac vous utilisez.

Codex normal ouvre un SSH interactif avec pseudo-terminal, rejoint le répertoire JARVIS et lance `codex`. À la fin, le shell distant est conservé. Codex sous tmux teste d’abord l’existence exacte, s’attache si la session existe, sinon crée/reprend avec `new-session -A` pour gérer une création concurrente. L’action « Retrouver » ne crée rien. Aucune session n’est supprimée, fusionnée ou détachée de force.

Pour quitter tmux en conservant le travail : `Ctrl+B`, puis `D`. Pour quitter le shell distant : `exit`. La fenêtre Terminal locale reste ouverte. Pour le tunnel, gardez sa fenêtre ouverte et ouvrez ensuite le lien JARVIS Web ; `Ctrl+C` arrête le tunnel. Son écoute est limitée à `127.0.0.1`, jamais au LAN. Le bouton web n’est pas un test de disponibilité.

Si le lanceur n’est pas installé, ouvrez **Copier**, puis collez la commande dans Terminal sur le Mac correspondant. En cas de presse-papiers refusé, le texte reste sélectionnable. Pour le lancement multiple de secours, collez chaque commande dans une fenêtre distincte ; le tunnel reste au premier plan.

## Configuration et actions autorisées

Le fichier [site/config.json](site/config.json) configure le site et sert de base à l’installation. Les profils partagent volontairement le même serveur ; les réglages peuvent différer par poste, notamment le port local du tunnel. Ces défauts proviennent des pistes fournies et de [l’audit](docs/AUDIT-JL-01.md), pas d’une validation SSH depuis les deux Macs.

La configuration native réelle est `~/Library/Application Support/JARVIS Launcher/config.json`. Elle possède aussi `clientProfile`, créé par l’installateur. **Changer le JSON du site ne change pas silencieusement la configuration des Macs.** Modifiez les deux copies volontairement si vous changez hôte, clé, sessions ou port local. Ne changez pas clientProfile pour contourner un matériel incompatible.

| Paramètre | Défaut / rôle |
|---|---|
| Serveur Tailscale | `adminjarvis@100.74.214.86` |
| Secours LAN | `adminjarvis@192.168.1.99`, action distincte |
| Clé | Chemin seul : `~/.ssh/id_ed25519_jarvis` ; aucun contenu de clé |
| Répertoire | `/home/adminjarvis/JARVIS` |
| Sessions proposées | `jarvis-codex`, `jarvis-13bc`, `jarvis-13f` ; existence réelle à vérifier |
| Tunnel | port local configurable → `127.0.0.1:8765` distant |
| `ui.sections` | Sections, ordre, labels, description, icône et IDs |
| `ui.favorites` | Favoris initiaux ; le navigateur conserve ensuite vos choix |

Pour récupérer les nouveaux favoris par défaut après modification du JSON, réinitialisez le stockage du site dans le navigateur. L’ajout d’un nom de session est autorisé uniquement si son format est sûr et qu’il figure dans la configuration locale. Ajouter un label ne crée pas de nouvelle action exécutable.

| ID | Action |
|---|---|
| `ssh` | SSH interactif JARVIS Tailscale |
| `ssh-lan` | SSH interactif JARVIS LAN explicite |
| `codex` | Codex distant, puis shell |
| `codex-tmux` | tmux : recherche exacte puis reprise/création Codex |
| `tmux-attach` | Attachement exact sans création |
| `tmux-list` | Liste puis shell |
| `web-tunnel` | Tunnel local au premier plan |
| `services` | État des trois services JARVIS, lecture seule |
| `workspace` | Liste fixe de trois terminaux |
| `check` | Diagnostic local sans SSH |

Format d’URL : `jarvis-launcher://launch/macbook-pro/codex-tmux?session=jarvis-codex`. Seuls profil, ID et session autorisée sont acceptés. Aucun argument `command`, `host`, `token` ou script libre.

## Dépannage et repli

| Situation | Comportement / action |
|---|---|
| Lanceur absent ou protocole refusé | Utiliser la copie ; réinstaller/enregistrer le protocole et autoriser le navigateur |
| Profil incorrect | Action native bloquée ; choisir le profil correspondant au matériel installé |
| Matériel non reconnu | Bloqué ; vérifier son nom dans system_profiler et ouvrir un ticket sans numéro de série |
| Clé absente | Native bloque avant Terminal ; corriger le chemin local ou préparer l’accès SSH habituel |
| Tailscale indisponible | Erreur SSH conservée dans Terminal ; se reconnecter au tailnet, ou choisir volontairement LAN |
| SSH absent/non joignable | Code d’erreur affiché, fenêtre laissée ouverte ; aucune cible réseau de secours automatique |
| Changement de clé d’hôte | Vérifier son empreinte avec une source de confiance, jamais désactiver StrictHostKeyChecking |
| Codex absent | Message et shell distant conservé ; aucune installation automatique |
| tmux absent | Message et shell distant conservé ; utiliser Codex normal après vérification |
| Session à retrouver absente | Message ; aucune création, suppression ou fusion |
| Tunnel : port local occupé | SSH échoue ; adapter localWebPort, par exemple 8766, dans la configuration locale et le site |
| Tunnel connecté mais web inaccessible | Vérifier le service distant et son port ; ExitOnForwardFailure ne prouve pas la disponibilité web |
| Presse-papiers bloqué | Sélection et copie manuelle ; garder les commandes visibles |
| Automatisation refusée | Réactiver le contrôle de Terminal dans Confidentialité et sécurité → Automatisation |

## Sécurité

Liste blanche native stricte, quoting POSIX, arguments bornés, confirmation locale obligatoire. N’importe quel site peut tenter d’invoquer une action connue : confirmez seulement vos propres clics. Aucun secret dans le dépôt ou les URL. Le chemin de clé reste un chemin public ; la clé privée reste sur le Mac.

SSH ignore les alias/ProxyCommand implicites via `-F /dev/null`, conserve la vérification des clés d’hôte, n’exporte pas l’agent/X11 et utilise un délai borné. Les commandes exécutées sont construites à partir de modèles fermés, jamais reçues depuis GitHub Pages. Aucun script JARVIS à dupliquer sur les clients. Le lanceur ne limite pas les actions ultérieures d’un utilisateur dans Codex ou le shell interactif.

Voir [architecture et menaces](docs/ARCHITECTURE.md), [tests](docs/TESTS.md), [réception réelle sur les Macs](docs/RECEPTION-MACOS.md).

## Build, tests et publication

Le frontend est utilisable sans build sur un hébergement statique. Les outils de développement emploient Python 3 uniquement pour tester/générer les livrables ; Python n’est pas une dépendance du lanceur macOS.

```bash
# Crée les fichiers Pages et le ZIP de sources, sans npm
python3 scripts/build.py

# Tests développeur, dans un environnement dédié
python3 -m venv .test-venv
.test-venv/bin/python -m pip install playwright
.test-venv/bin/python -m playwright install chromium
.test-venv/bin/python tests/test_launcher.py

# Sur macOS : compilation et politique JXA, sans SSH ni Terminal
bash tests/macos-smoke.sh
```

Sur Debian, python3-venv/pip peuvent être nécessaires pour les tests. Aucun paquet système de JARVIS n’a été installé pour cette mission ; les tests ont utilisé un interpréteur et Playwright préexistants en lecture, avec écriture de bytecode désactivée.

La suite démarre un serveur statique temporaire sur loopback pour la QA et l’arrête à la fin ; ce serveur n’appartient pas à l’architecture déployée. Les actions tmux/Codex sont simulées dans un dossier isolé ; un seul échec OpenSSH réel est testé vers un port loopback inutilisé, jamais vers JARVIS.

Publication préparée sur `codex/jl-01-jarvis-launcher`, PR vers main, Pages sur `gh-pages`. [Instructions exactes et script](docs/PUBLICATION.md). GitHub Pages gratuit nécessite ici un dépôt public. Ne fusionnez pas la PR automatiquement.

## Désinstallation

```bash
bash macos/uninstall.sh
```

Confirmation puis déplacement de l’application dans la Corbeille. La configuration locale, les clés SSH, anciens scripts, sauvegardes et sessions tmux sont conservés. Pour retirer ensuite la configuration, supprimez volontairement son dossier dans Finder ; cela n’est pas automatique. Les préférences locales du site peuvent être retirées via les réglages du navigateur. Aucun service à arrêter.

## Structure

```text
site/       HTML, CSS, JavaScript et config JSON
macos/      AppleScript, JXA, installation/désinstallation
scripts/    Build et publication optionnelle
tests/      Politique, navigateur, shells isolés, smoke test macOS
docs/       Audit, architecture, tests, preuves, réception, rapport, PR
dist/       Pages, ZIP, bundle Git et empreintes SHA-256 (générés)
```

Licence MIT, composants natifs gratuits. Les résultats réels et limites sont documentés dans [RAPPORT-JL-01.md](docs/RAPPORT-JL-01.md). Aucun fichier du dépôt principal ou de l’installation JARVIS n’a été modifié.
