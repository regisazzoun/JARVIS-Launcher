(function () {
  var results = [];
  var base = window.testConfig;
  function copy() { return JSON.parse(JSON.stringify(base)); }
  function test(name, body) { try { body(); results.push({ name: name, ok: true }); } catch (e) { results.push({ name: name, ok: false, error: String(e) }); } }
  function assert(value, message) { if (!value) throw new Error(message || 'Assertion failed'); }
  function throws(body) { var failed = false; try { body(); } catch (_) { failed = true; } assert(failed, 'Rejet attendu'); }
  ['macbook-pro', 'mac-mini'].forEach(function (profile) {
    ['ssh', 'ssh-lan', 'codex', 'codex-tmux', 'tmux-attach', 'tmux-list', 'web-tunnel', 'services', 'workspace', 'check'].forEach(function (action) {
      test(profile + ': ' + action, function () {
        var url = JarvisCore.buildURL(profile, action, 'jarvis-13f');
        var plan = JarvisCore.planFromURL(copy(), url, profile, profile);
        assert(plan.commands.length === (action === 'workspace' ? 3 : action === 'check' ? 0 : 1));
        plan.commands.forEach(function (c) {
          assert(c.ssh.indexOf("'-F' '/dev/null'") >= 0); assert(c.ssh.indexOf('StrictHostKeyChecking=ask') >= 0);
          assert(c.ssh.indexOf('ForwardAgent=no') >= 0); assert(c.ssh.indexOf('127.0.0.1:8765:127.0.0.1:8765') >= 0 || c.ssh.indexOf(' -tt ') >= 0);
          assert(c.terminal.indexOf('jarvis_launcher_rc=$?') >= 0); assert(c.terminal.indexOf('exec /usr/bin/ssh') < 0);
          assert(c.ssh.indexOf('adminjarvis@' + (action === 'ssh-lan' ? '192.168.1.99' : '100.74.214.86')) >= 0);
        });
      });
    });
    test(profile + ': mauvais profil installé', function () { throws(function () { JarvisCore.planFromURL(copy(), JarvisCore.buildURL(profile, 'ssh'), profile === 'mac-mini' ? 'macbook-pro' : 'mac-mini', profile); }); });
    test(profile + ': matériel incorrect', function () { throws(function () { JarvisCore.planFromURL(copy(), JarvisCore.buildURL(profile, 'ssh'), profile, 'unknown'); }); });
    test(profile + ': sessions exactes', function () {
      var p = JarvisCore.preview(copy(), profile, 'codex-tmux', 'jarvis-13f').commands[0]; assert(p.remote.indexOf("'=jarvis-13f'") >= 0); assert(p.remote.indexOf('new-session -A') >= 0); assert(p.remote.indexOf('kill-session') < 0);
    });
  });
  [
    '', 'https://launch/mac-mini/ssh', 'jarvis-launcher://launch/mac-mini/ssh\n',
    'jarvis-launcher://launch/mac-mini/ssh?command=rm', 'jarvis-launcher://launch/mac-mini/ssh?host=evil.example',
    'jarvis-launcher://launch/mac-mini/ssh?session=jarvis-codex', 'jarvis-launcher://launch/mac-mini/ssh#fragment',
    'jarvis-launcher://launch/mac-mini/codex-tmux?session=jarvis-codex&session=other',
    'jarvis-launcher://launch/mac-mini/codex-tmux?session=jarvis-codex;touch%20/tmp/pwn',
    'jarvis-launcher://launch/mac-mini/codex-tmux?session=$(id)', 'jarvis-launcher://launch/mac-mini/codex-tmux?session=`id`',
    'jarvis-launcher://launch/mac-mini/codex-tmux?session=%0A', 'jarvis-launcher://launch/mac-mini/codex-tmux?session=../../etc/passwd',
    'jarvis-launcher://launch/mac-mini/../../ssh', 'jarvis-launcher://user@launch/mac-mini/ssh',
    'jarvis-launcher://launch:80/mac-mini/ssh', 'jarvis-launcher://launch/mac-mini/constructor',
    'jarvis-launcher://launch/mac-mini/__proto__', 'jarvis-launcher://launch/mac-mini/arbitrary',
    'jarvis-launcher://launch/other/ssh', 'jarvis-launcher://launch/mac-mini/ssh/',
    'jarvis-launcher://launch/mac-mini/codex-tmux?session=' + 'a'.repeat(41),
    'jarvis-launcher://launch/mac-mini/ssh?token=secret', 'jarvis-launcher://launch/mac-mini/ssh\u0000'
  ].forEach(function (url, i) { test('URL hostile ' + i, function () { throws(function () { JarvisCore.parseURL(url); }); }); });
  test('Session non autorisée localement', function () { throws(function () { JarvisCore.planFromURL(copy(), 'jarvis-launcher://launch/mac-mini/tmux-attach?session=unknown', 'mac-mini', 'mac-mini'); }); });
  var mutations = [
    function (c) { c.profiles['mac-mini'].host = 'server;touch /tmp/pwn'; },
    function (c) { c.profiles['mac-mini'].host = '-oProxyCommand=id'; },
    function (c) { c.profiles['mac-mini'].user = 'user$(id)'; },
    function (c) { c.profiles['mac-mini'].identityFile = '~/.ssh/key";id'; },
    function (c) { c.profiles['mac-mini'].identityFile = '~/.ssh/../../secret'; },
    function (c) { c.profiles['mac-mini'].localWebPort = 80; },
    function (c) { c.profiles['mac-mini'].localWebPort = '8765;id'; },
    function (c) { c.remote.directory = '/tmp/x;id'; },
    function (c) { c.remote.directory = '/home/../tmp'; },
    function (c) { c.remote.directory = '/tmp/x\n'; },
    function (c) { c.remote.sessions = ['jarvis;id']; },
    function (c) { c.remote.defaultSession = 'missing'; },
    function (c) { delete c.profiles['mac-mini']; },
    function (c) { c.profiles['mac-mini'].sshPort = 2222; }
  ];
  mutations.forEach(function (mutate, i) { test('Configuration hostile ' + i, function () { var c = copy(); mutate(c); throws(function () { JarvisCore.validateConfig(c); }); }); });
  test('Port local distinct pour Mac mini', function () { var c = copy(); c.profiles['mac-mini'].localWebPort = 8766; assert(JarvisCore.preview(c, 'mac-mini', 'web-tunnel').commands[0].ssh.indexOf('127.0.0.1:8766:127.0.0.1:8765') >= 0); assert(JarvisCore.preview(c, 'macbook-pro', 'web-tunnel').commands[0].ssh.indexOf('127.0.0.1:8765:127.0.0.1:8765') >= 0); });
  test('Quoting apostrophe', function () { assert(JarvisCore.quote("a'b") === "'a'\\''b'"); });
  return results;
}());
