import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('portable_installer', ROOT / 'tools/install_portable.py')
portable = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portable)
spec2 = importlib.util.spec_from_file_location('portable_forge', ROOT / 'tools/skill_engine.py')
forge = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(forge)
spec3 = importlib.util.spec_from_file_location('fes_funnel5', ROOT / 'tools/funnel.py')
funnel = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(funnel)


class PortableInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_every_agent_has_documented_separate_path(self):
        locations = {
            'codex': '.agents/skills', 'claude': '.claude/skills', 'cursor': '.cursor/skills',
            'gemini': '.gemini/skills', 'copilot': '.github/skills', 'opencode': '.opencode/skills'
        }
        for host, rel in locations.items():
            with self.subTest(host=host):
                self.assertEqual(portable.destinations(host, 'project', self.root), [self.root / rel])
        self.assertEqual(len(portable.destinations('all', 'project', self.root)), 2)

    def test_dry_run_no_mutations(self):
        actions = portable.install('all', 'project', self.root, 'rescue', dry_run=True)
        self.assertTrue(actions)
        self.assertFalse((self.root / '.agents').exists())
        self.assertFalse((self.root / '.claude').exists())

    def test_every_agent_installs_skill_validly(self):
        for host in portable.AGENTS:
            with self.subTest(host=host):
                with tempfile.TemporaryDirectory() as d:
                    target = Path(d)
                    results = portable.install(host, 'project', target, 'core')
                    self.assertEqual(len(results), 2 * 9 if host == 'all' else 9)
                    for base in portable.destinations(host, 'project', target):
                        body = (base / 'funnel-engineer' / 'SKILL.md').read_text()
                        self.assertIn('name: funnel-engineer', body)

    def test_unchanged_reinstall_idempotent(self):
        portable.install('codex', 'project', self.root, 'core')
        results = portable.install('codex', 'project', self.root, 'core')
        self.assertEqual({row['result'] for row in results}, {'unchanged'})

    def test_conflict_no_overwrite_then_backup(self):
        target = self.root / '.cursor/skills/funnel-engineer/SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_text('CUSTOM SKILL\n')
        results = portable.install('cursor', 'project', self.root, 'core')
        self.assertTrue(any(r['result'] == 'skipped_conflict' for r in results))
        self.assertEqual(target.read_text(), 'CUSTOM SKILL\n')
        results = portable.install('cursor', 'project', self.root, 'core', upgrade=True)
        self.assertTrue(any('upgraded_backup=' in r['result'] for r in results))
        backups = list(target.parent.parent.glob('funnel-engineer.fes-v5-backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'SKILL.md').read_text(), 'CUSTOM SKILL\n')
        self.assertIn('name: funnel-engineer', target.read_text())

    def test_symlink_target_rejected(self):
        (self.root / 'outside').mkdir()
        (self.root / '.agents').symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaises(portable.InstallError):
            portable.install('codex', 'project', self.root, 'core')
        self.assertFalse(any((self.root / 'outside').iterdir()))

    def test_roles_only_codex_and_main_config_untouched(self):
        with self.assertRaises(portable.InstallError):
            portable.install('claude', 'project', self.root, codex_roles=True)
        cfg = self.root / '.codex/config.toml'
        cfg.parent.mkdir(parents=True)
        cfg.write_text('model = "do-not-change"\n')
        results = portable.install('codex', 'project', self.root, 'core', codex_roles=True)
        self.assertEqual(cfg.read_text(), 'model = "do-not-change"\n')
        self.assertTrue((self.root / '.codex/agents/fes_architect.toml').exists())
        self.assertTrue((self.root / '.codex/fes-v5-config-snippet.toml').exists())
        self.assertEqual(len([r for r in results if 'role' in r]), 5)

    def test_profiles_differ_and_validate_names(self):
        full = portable.install('gemini', 'project', self.root, 'full', dry_run=True)
        rescue = portable.install('gemini', 'project', self.root, 'rescue', dry_run=True)
        self.assertEqual(len(full), 22)
        self.assertEqual(len(rescue), 11)
        self.assertTrue({'fes-vibe-hardening', 'fes-security'} <= {r['skill'] for r in rescue})


class PortableSkillForgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        funnel.new_task(self.root, 'portability', 'build')
        draft = self.root / '.funnel/skill-drafts/method.md'
        draft.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text('1. Inspect user-provided application contracts before editing.\n'
                         '2. Confirm failure on a disposable local fixture, then write a test.\n'
                         '3. Apply the narrowest scoped change and rerun all affected tests.\n')
        self.draft = draft.relative_to(self.root).as_posix()

    def test_claude_project_forge_and_checksum(self):
        result = forge.forge(self.root, 'portability', 'claude-workflow',
            'Use for project specific regression correction steps in Claude',
            'When a Claude-only app needs a narrow tested workflow',
            'When the change can be performed using existing skills', self.draft,
            'Rerun the actual unit test and report passing outputs',
            'Missing a repeatable app-specific correction procedure', host='claude')
        self.assertTrue((self.root / '.claude/skills' / result['name'] / 'SKILL.md').is_file())
        self.assertTrue(forge.verify(self.root, 'portability')['valid'])
        entry = self.root / result['path']
        entry.write_text(entry.read_text() + '\nMODIFIED')
        self.assertFalse(forge.verify(self.root, 'portability')['valid'])

    def test_inventory_detects_native_host_skills(self):
        path = self.root / '.cursor/skills/domain-check/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('---\nname: domain-check\ndescription: Verify this app domain workflow.\n---\n')
        rows = forge.inventory(self.root)
        self.assertTrue(any(x['name'] == 'domain-check' and x['scope'] == 'project-cursor' for x in rows))

    def test_cursor_native_forge(self):
        result = forge.forge(self.root, 'portability', 'cursor-method',
            'Use for project specific regression correction steps in Cursor',
            'When a Cursor-only app needs a narrow tested workflow',
            'When the change can be performed using existing skills', self.draft,
            'Rerun the actual unit test and report passing outputs',
            'Missing a repeatable app-specific correction procedure', host='cursor')
        self.assertTrue((self.root / '.cursor/skills' / result['name'] / 'SKILL.md').is_file())
        self.assertTrue(forge.verify(self.root, 'portability')['valid'])

    def test_unknown_host_rejected(self):
        with self.assertRaises(forge.SkillError):
            forge.forge(self.root, 'portability', 'invalid-host',
                'Use for project specific regression correction steps',
                'When this missing project skill is necessary',
                'When another existing skill covers the request', self.draft,
                'Run relevant local tests and verify actual results',
                'Needed for a real repeatable domain-specific gap', host='everything')

if __name__ == '__main__':
    unittest.main()
