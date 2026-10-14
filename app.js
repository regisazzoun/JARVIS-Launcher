(function () {
  'use strict';
  var config, profile = 'macbook-pro', favorites = [], toastTimer;
  var isMac = /Mac/.test(navigator.platform) && !(navigator.maxTouchPoints > 1);
  var isMobile = /iPhone|iPad|Android/.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && /Mac/.test(navigator.platform));
  function stored(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch (_) { return fallback; } }
  function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* Private browsing still works. */ } }
  function node(tag, className, text) { var n = document.createElement(tag); if (className) n.className = className; if (text !== undefined) n.textContent = text; return n; }
  function toast(message) { var n = document.getElementById('toast'); n.textContent = message; n.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(function () { n.hidden = true; }, 5000); }
  function session() { return document.getElementById('session').value; }
  function plan(action) { return JarvisCore.preview(config, profile, action, session()); }
  function openCommand(action) {
    document.getElementById('command-heading').textContent = action === 'workspace' ? 'Trois commandes, trois terminaux' : 'Copier dans Terminal';
    document.getElementById('command-text').value = plan(action).commands.map(function (c) { return c.ssh; }).join('\n\n');
    document.getElementById('clipboard-note').textContent = action === 'workspace' ? 'Copiez chaque commande dans une fenêtre distincte. Le tunnel bloque volontairement le terminal.' : '';
    document.getElementById('command-dialog').showModal();
  }
  function launch(action) {
    if (!isMac || isMobile) { openCommand(action); return; }
    window.location.href = JarvisCore.buildURL(profile, action, (action === 'codex-tmux' || action === 'tmux-attach') ? session() : null);
    toast('Demande envoyée au lanceur local. Sa réception n’est pas vérifiable ici.');
  }
  function actions() { return config.ui.sections.reduce(function (all, s) { return all.concat(s.actions); }, []); }
  function card(action) {
    var a = node('article', 'action-card'); a.dataset.action = action.id;
    var top = node('div', 'card-top'); top.appendChild(node('span', 'action-icon', action.icon || '↗'));
    var favorite = node('button', 'favorite', favorites.indexOf(action.id) >= 0 ? '★' : '☆'); favorite.type = 'button';
    favorite.setAttribute('aria-label', 'Favori : ' + action.label); favorite.setAttribute('aria-pressed', String(favorites.indexOf(action.id) >= 0));
    favorite.addEventListener('click', function () { var index = favorites.indexOf(action.id); if (index >= 0) favorites.splice(index, 1); else favorites.push(action.id); store('jarvis-launcher:favorites', favorites); render(); var target = document.querySelector('[data-action="' + action.id + '"] .favorite'); if (target) target.focus(); });
    top.appendChild(favorite); a.appendChild(top); a.appendChild(node('h3', '', action.label)); a.appendChild(node('p', '', action.description));
    var buttons = node('div', 'card-actions'); var open = node('button', 'launch-button'); open.type = 'button';
    open.appendChild(node('span', '', isMac && !isMobile ? 'Ouvrir Terminal' : 'Afficher la commande')); open.appendChild(node('span', '', '↗')); open.setAttribute('aria-label', (isMac && !isMobile ? 'Ouvrir Terminal : ' : 'Afficher la commande : ') + action.label);
    open.addEventListener('click', function () { launch(action.id); });
    var copy = node('button', 'copy-button', 'Copier'); copy.type = 'button'; copy.setAttribute('aria-label', 'Copier la commande : ' + action.label); copy.addEventListener('click', function () { openCommand(action.id); });
    buttons.appendChild(open); buttons.appendChild(copy); a.appendChild(buttons); return a;
  }
  function section(title, description, entries, number) {
    var s = node('section', 'action-section'); var h = node('div', 'section-heading'), words = node('div'); words.appendChild(node('h2', '', title)); words.appendChild(node('p', '', description)); h.appendChild(words); h.appendChild(node('span', 'section-number', number)); s.appendChild(h);
    var grid = node('div', 'cards'); entries.forEach(function (a) { grid.appendChild(card(a)); }); s.appendChild(grid); return s;
  }
  function render() {
    document.getElementById('profile-description').textContent = 'Poste client : ' + config.profiles[profile].label + '. Un seul serveur : JARVIS.';
    document.querySelectorAll('[data-profile]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.profile === profile)); });
    var container = document.getElementById('actions'); container.replaceChildren();
    var favoriteActions = favorites.map(function (id) { return actions().find(function (a) { return a.id === id; }); }).filter(Boolean);
    if (favoriteActions.length) container.appendChild(section('Vos favoris', 'Les chemins que vous empruntez le plus.', favoriteActions, '★'));
    config.ui.sections.forEach(function (s, i) { container.appendChild(section(s.title, s.description, s.actions, '0' + (i + 1))); });
    var web = document.getElementById('web-link'); web.href = 'http://127.0.0.1:' + config.profiles[profile].localWebPort + '/';
    document.getElementById('workspace').textContent = isMac && !isMobile ? 'Ouvrir mon espace ↗' : 'Commandes de mon espace ↗';
  }
  async function start() {
    try {
      var response = await fetch('config.json', { cache: 'no-store' }); if (!response.ok) throw new Error('Configuration inaccessible');
      config = JarvisCore.validateConfig(await response.json());
      if (!Array.isArray(config.ui.sections) || config.ui.sections.length > 10) throw new Error('Sections invalides');
      config.ui.sections.forEach(function (s) { if (!Array.isArray(s.actions) || s.actions.length > 20) throw new Error('Actions invalides'); s.actions.forEach(function (a) { if (JarvisCore.actions.indexOf(a.id) < 0 || ['check', 'workspace'].indexOf(a.id) >= 0) throw new Error('Action non autorisée : ' + a.id); }); });
      profile = stored('jarvis-launcher:profile', 'macbook-pro'); if (JarvisCore.profiles.indexOf(profile) < 0) profile = 'macbook-pro';
      favorites = stored('jarvis-launcher:favorites', config.ui.favorites || []); if (!Array.isArray(favorites)) favorites = [];
      favorites = favorites.filter(function (id) { return actions().some(function (a) { return a.id === id; }); });
      document.title = config.ui.title || 'JARVIS Launcher';
      var select = document.getElementById('session'); config.remote.sessions.forEach(function (s) { var opt = node('option', '', s); opt.value = s; select.appendChild(opt); });
      var selected = stored('jarvis-launcher:session', config.remote.defaultSession); select.value = config.remote.sessions.indexOf(selected) >= 0 ? selected : config.remote.defaultSession;
      select.addEventListener('change', function () { store('jarvis-launcher:session', session()); });
      document.querySelectorAll('[data-profile]').forEach(function (b) { b.addEventListener('click', function () { profile = b.dataset.profile; store('jarvis-launcher:profile', profile); render(); }); });
      document.getElementById('workspace').addEventListener('click', function () { if (isMac && !isMobile) document.getElementById('workspace-dialog').showModal(); else openCommand('workspace'); });
      document.getElementById('confirm-workspace').addEventListener('click', function () { document.getElementById('workspace-dialog').close(); launch('workspace'); });
      document.getElementById('check-launcher').disabled = !isMac || isMobile;
      document.getElementById('check-launcher').addEventListener('click', function () { launch('check'); });
      if (isMobile || !isMac) {
        document.getElementById('launcher-note').textContent = isMobile ? 'Sur mobile : copie uniquement, Terminal.app n’est pas accessible.' : 'Ce poste n’est pas macOS : les commandes restent disponibles à copier.';
        document.getElementById('web-link').hidden = true;
        document.getElementById('environment-note').textContent = 'Commandes à copier sur le Mac sélectionné. Ce navigateur ne peut pas vérifier le matériel ni ouvrir Terminal.app.';
      }
      document.getElementById('copy-dialog').addEventListener('click', async function () {
        var value = document.getElementById('command-text').value;
        try { if (!navigator.clipboard || !window.isSecureContext) throw new Error('Clipboard unavailable'); await navigator.clipboard.writeText(value); document.getElementById('clipboard-note').textContent = 'Copié. Collez dans Terminal sur ' + config.profiles[profile].label + '.'; }
        catch (_) { var t = document.getElementById('command-text'); t.focus(); t.select(); document.getElementById('clipboard-note').textContent = 'Copie automatique indisponible. Utilisez ⌘C ou la copie manuelle du texte sélectionné.'; }
      });
      document.querySelectorAll('.dialog-close').forEach(function (b) { b.addEventListener('click', function () { b.closest('dialog').close(); }); });
      render();
    } catch (error) {
      var err = document.getElementById('load-error'); err.hidden = false; err.textContent = 'Chargement impossible : ' + error.message + '. Aucune action lancée. Consultez le guide.';
      document.querySelectorAll('[data-profile], #workspace, #check-launcher').forEach(function (b) { b.disabled = true; });
    }
  }
  start();
}());
