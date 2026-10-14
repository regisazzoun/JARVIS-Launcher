"""Isolated browser and shell tests. Never invokes the deployed Codex or tmux."""
import functools
import http.server
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import tempfile
import threading
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'site/config.json').read_text())
RESULTS = ROOT / 'test-results'

class PagesHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'site'), **kwargs)

    def do_GET(self):
        if not self.path.startswith('/JARVIS-Launcher/'):
            self.send_error(404)
            return
        self.path = self.path[len('/JARVIS-Launcher'):]
        super().do_GET()

    def log_message(self, *_):
        pass

class LauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RESULTS.mkdir(exist_ok=True)
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), PagesHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/JARVIS-Launcher/'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)
        cls.policy = cls.browser.new_page()
        cls.policy.goto(cls.url)
        cls.policy.wait_for_selector('[data-action="ssh"]')

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def preview(self, action, profile='macbook-pro', config=None, session=None):
        return self.policy.evaluate('(args) => JarvisCore.preview(args.c, args.p, args.a, args.s)', {'c': config or CONFIG, 'p': profile, 'a': action, 's': session})

    def test_policy_injection_profiles_and_quote(self):
        self.policy.evaluate('(c) => window.testConfig = c', CONFIG)
        results = self.policy.evaluate((ROOT / 'tests/core-tests.js').read_text())
        (RESULTS / 'policy-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
        self.assertGreaterEqual(len(results), 65)
        self.assertEqual([r for r in results if not r['ok']], [])

    def test_desktop_profiles_persistence_favorites_copy(self):
        context = self.browser.new_context(viewport={'width': 1440, 'height': 1050})
        context.add_init_script("Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'}); Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});")
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(self.url)
        page.wait_for_selector('[data-action="ssh"]')
        self.assertIn('MacBook Pro', page.locator('#profile-description').inner_text())
        page.locator('[data-profile="mac-mini"]').click()
        page.locator('#session').select_option('jarvis-13f')
        page.reload()
        page.wait_for_selector('[data-action="ssh"]')
        self.assertEqual(page.locator('[data-profile="mac-mini"]').get_attribute('aria-pressed'), 'true')
        self.assertEqual(page.locator('#session').input_value(), 'jarvis-13f')
        page.locator('[data-action="codex-tmux"] .copy-button').first.click()
        value = page.locator('#command-text').input_value()
        self.assertIn('jarvis-13f', value)
        self.assertIn(' -tt ', value)
        self.assertIn('new-session -A', value)
        page.locator('#command-dialog .dialog-close').click()
        page.locator('[data-action="ssh"] .favorite').first.click()
        self.assertEqual(page.locator('[data-action="ssh"] .favorite').first.get_attribute('aria-pressed'), 'false')
        page.locator('#workspace').click()
        self.assertTrue(page.locator('#workspace-dialog').is_visible())
        page.locator('#workspace-dialog .dialog-close').click()
        page.screenshot(path=str(RESULTS / 'desktop.png'), full_page=True)
        self.assertEqual(errors, [])
        context.close()

    def test_protocol_request_from_pages_path(self):
        context = self.browser.new_context()
        context.add_init_script("Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'}); Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});")
        page = context.new_page()
        page.goto(self.url)
        page.wait_for_selector('[data-action="ssh"]')
        page.evaluate('''() => { window.emittedURLs=[]; const original=JarvisCore.buildURL; JarvisCore.buildURL=function(p,a,s){ const u=original(p,a,s);window.emittedURLs.push(u);return u; }; }''')
        page.locator('#check-launcher').click()
        self.assertEqual(page.evaluate('window.emittedURLs'), ['jarvis-launcher://launch/macbook-pro/check'])
        self.assertIn('État non vérifiable', page.locator('.connection').inner_text())
        (RESULTS / 'protocol-request.json').write_text(json.dumps({'origin': 'local simulation of /JARVIS-Launcher/', 'emitted': page.evaluate('window.emittedURLs'), 'macOS_handler_invoked': False}, indent=2))
        context.close()

    def test_mobile_copy_only_and_no_overflow(self):
        for name, width, height, ua, platform in [('iphone', 390, 844, 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)', 'iPhone'), ('ipad', 820, 1180, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)', 'MacIntel')]:
            with self.subTest(device=name):
                context = self.browser.new_context(viewport={'width': width, 'height': height}, user_agent=ua, has_touch=True)
                context.add_init_script(f"Object.defineProperty(navigator, 'platform', {{get: () => {json.dumps(platform)}}}); Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => 5}});")
                page = context.new_page()
                page.goto(self.url)
                page.wait_for_selector('[data-action="ssh"]')
                self.assertTrue(page.locator('#check-launcher').is_disabled())
                self.assertTrue(page.locator('#web-link').is_hidden())
                page.locator('[data-action="ssh"] .launch-button').first.click()
                self.assertTrue(page.locator('#command-dialog').is_visible())
                self.assertIn('adminjarvis@100.74.214.86', page.locator('#command-text').input_value())
                page.locator('#command-dialog .dialog-close').click()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.screenshot(path=str(RESULTS / f'{name}.png'), full_page=True)
                context.close()

    def test_unavailable_storage_clipboard_and_config(self):
        context = self.browser.new_context()
        context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}});Object.defineProperty(navigator,'clipboard',{value:undefined});")
        page = context.new_page()
        page.goto(self.url)
        page.wait_for_selector('[data-action="ssh"]')
        page.locator('[data-action="ssh"] .copy-button').first.click()
        page.locator('#copy-dialog').click()
        self.assertIn('Copie automatique indisponible', page.locator('#clipboard-note').inner_text())
        context.close()
        context = self.browser.new_context()
        context.route('**/config.json', lambda route: route.fulfill(status=503, body='not available'))
        page = context.new_page()
        page.goto(self.url)
        page.locator('#load-error').wait_for(state='visible')
        self.assertIn('Aucune action lancée', page.locator('#load-error').inner_text())
        self.assertTrue(page.locator('#workspace').is_disabled())
        context.close()

    def test_json_labels_are_text_not_html_and_unknown_actions_refused(self):
        c = json.loads(json.dumps(CONFIG))
        c['ui']['sections'][0]['actions'][0]['label'] = '<img src=x onerror=alert(1)>'
        context = self.browser.new_context()
        context.route('**/config.json', lambda route: route.fulfill(json=c))
        page = context.new_page()
        page.goto(self.url)
        page.wait_for_selector('[data-action="ssh"]')
        self.assertEqual(page.locator('#actions img').count(), 0)
        self.assertIn('<img src=x', page.locator('[data-action="ssh"] h3').first.inner_text())
        context.close()
        c['ui']['sections'][0]['actions'][0]['id'] = 'arbitrary-command'
        context = self.browser.new_context()
        context.route('**/config.json', lambda route: route.fulfill(json=c))
        page = context.new_page()
        page.goto(self.url)
        page.locator('#load-error').wait_for(state='visible')
        self.assertIn('Action non autorisée', page.locator('#load-error').inner_text())
        context.close()

    def test_generated_shell_syntax_and_ssh_failure_window_kept(self):
        for profile in CONFIG['profiles']:
            for action in ['ssh', 'ssh-lan', 'codex', 'codex-tmux', 'tmux-attach', 'tmux-list', 'web-tunnel', 'services', 'workspace']:
                for command in self.preview(action, profile)['commands']:
                    checked = subprocess.run(['/bin/bash', '-n'], input=command['terminal'], text=True, capture_output=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    if command['remote']:
                        remote_argv = shlex.split(shlex.split(command['ssh'])[-1])
                        self.assertEqual(remote_argv, ['bash', '-lc', command['remote']])
                        self.assertEqual(subprocess.run(['/bin/bash', '-n'], input=command['remote'], text=True, capture_output=True).returncode, 0)
        with tempfile.TemporaryDirectory(prefix='jl-ssh-') as directory:
            fake = Path(directory) / 'ssh'
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "Simulated connection failure"\nexit 255\n')
            fake.chmod(0o700)
            command = self.preview('ssh')['commands'][0]['terminal'].replace("'/usr/bin/ssh'", shlex.quote(str(fake)), 1)
            result = subprocess.run(['/bin/bash', '-c', command + '; printf "%s\\n" LOCAL_SHELL_AVAILABLE'], text=True, capture_output=True, timeout=5)
            self.assertIn('code 255', result.stdout)
            self.assertIn('LOCAL_SHELL_AVAILABLE', result.stdout)
            self.assertIn('Aucun repli réseau automatique', result.stdout)
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
            # Bound but not listening: real OpenSSH fails without contacting JARVIS.
            failure = subprocess.run(['/usr/bin/ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=2', '-p', str(port), '127.0.0.1'], capture_output=True, text=True, timeout=5)
            self.assertEqual(failure.returncode, 255)
            (RESULTS / 'ssh-failure.json').write_text(json.dumps({'returncode': failure.returncode, 'target': 'loopback unused port', 'stderr': failure.stderr}, indent=2))

    def test_tmux_branches_and_missing_tools_in_isolation(self):
        scenarios = [('codex-tmux', True, True, True, 'attach-session'), ('codex-tmux', False, True, True, 'new-session -A'), ('tmux-attach', False, True, True, 'Session absente'), ('tmux-list', False, True, True, 'list-sessions'), ('codex', False, True, False, 'Codex indisponible'), ('codex-tmux', False, False, True, 'tmux indisponible'), ('codex-tmux', False, True, False, 'aucune session créée')]
        for action, exists, has_tmux, has_codex, expected in scenarios:
            with self.subTest(action=action, exists=exists, has_tmux=has_tmux, has_codex=has_codex), tempfile.TemporaryDirectory(prefix='jl-remote-') as directory:
                root = Path(directory)
                log = root / 'calls.txt'
                stub = root / 'bin'
                stub.mkdir()
                scripts = {'bash': '#!/bin/sh\nprintf "%s\\n" SHELL_AVAILABLE\n'}
                if has_codex:
                    scripts['codex'] = '#!/bin/sh\nprintf "%s\\n" CODEX_CALLED\n'
                if has_tmux:
                    scripts['tmux'] = '#!/bin/sh\nprintf "%s\\n" "$*" >> "$JL_TEST_LOG"\nif [ "$1" = has-session ]; then exit ' + ('0' if exists else '1') + '; fi\nexit 0\n'
                for name, source in scripts.items():
                    (stub / name).write_text(source)
                    (stub / name).chmod(0o700)
                c = json.loads(json.dumps(CONFIG))
                c['remote']['directory'] = directory
                command = self.preview(action, config=c)['commands'][0]['remote']
                env = dict(os.environ, PATH=str(stub), JL_TEST_LOG=str(log))
                result = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-c', command], env=env, capture_output=True, text=True, timeout=5)
                combined = result.stdout + (log.read_text() if log.exists() else '')
                self.assertIn(expected, combined)
                self.assertIn('SHELL_AVAILABLE', combined)
                self.assertNotIn('kill-session', combined)
                if action == 'tmux-attach' and not exists:
                    self.assertNotIn('new-session', combined)

    def test_guide_keyboard_and_layout(self):
        page = self.browser.new_page(viewport={'width': 390, 'height': 844})
        page.goto(self.url + 'guide.html')
        self.assertIn('Votre Mac', page.locator('h1').inner_text())
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        page.goto(self.url)
        page.wait_for_selector('[data-action="ssh"]')
        page.keyboard.press('Tab')
        self.assertEqual(page.evaluate('document.activeElement.textContent'), 'Aller aux actions')
        page.close()

if __name__ == '__main__':
    unittest.main(verbosity=2)
