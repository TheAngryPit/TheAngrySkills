import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CREATE = Path(__file__).resolve().parents[1] / 'skills/engineering/docs-skill-builder/scripts/create-docs-skill.sh'


@unittest.skipUnless(sys.platform != 'win32' and shutil.which('bash'), 'requires POSIX symlink semantics and Bash')
class DocsSkillBuilderSecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='docs-skill-security-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'README.md').write_text('Synthetic documentation.\n')
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        subprocess.run(['git', '-C', str(self.source), 'add', 'README.md'], check=True)
        subprocess.run(['git', '-C', str(self.source), '-c', 'user.name=Synthetic fixture',
                        '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        self.output = self.root / 'generated'

    def scaffold(self, paths, tool_name='Fixture', source_url='https://example.invalid/fixture.git'):
        command = ['bash', str(CREATE), '--name', 'fixture-docs', '--tool-name', tool_name,
                   '--source-url', source_url, '--output', str(self.output)]
        for path in paths:
            command.extend(['--doc-path', path])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def generate(self):
        env = dict(os.environ, DOCS_SOURCE_DIR_OVERRIDE=str(self.source))
        return subprocess.run(['bash', str(self.output / 'scripts/generate-docs-skill.sh')],
                              env=env, capture_output=True, text=True)

    def test_regular_documents_and_reserved_index_preserve_original_bytes(self):
        original = b'Original upstream index.\n'
        (self.source / 'INDEX.md').write_bytes(original)
        docs = self.source / 'docs'
        docs.mkdir()
        (docs / 'guide with spaces.md').write_bytes(b'Nested documentation.\n')
        self.scaffold(['README.md', 'INDEX.md', 'docs'])
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        references = self.output / 'skills/fixture-docs/references'
        self.assertEqual((references / 'README.md').read_bytes(), b'Synthetic documentation.\n')
        self.assertEqual((references / 'INDEX.source.md').read_bytes(), original)
        self.assertEqual((references / 'docs/guide with spaces.md').read_bytes(), b'Nested documentation.\n')
        self.assertIn('Documentation References', (references / 'INDEX.md').read_text())

    def test_symlinked_index_cannot_overwrite_an_external_file(self):
        target = self.root / 'outside.md'
        target.write_bytes(b'Outside sentinel.\n')
        (self.source / 'INDEX.md').symlink_to(target)
        self.scaffold(['INDEX.md'])
        result = self.generate()
        self.assertEqual(target.read_bytes(), b'Outside sentinel.\n')
        self.assertNotEqual(result.returncode, 0)

    def test_symlinked_output_parent_cannot_replace_an_external_directory(self):
        self.scaffold(['README.md'])
        shutil.rmtree(self.output / 'skills')
        target = self.root / 'outside'
        protected = target / 'fixture-docs/sentinel.txt'
        protected.parent.mkdir(parents=True)
        protected.write_bytes(b'Preserve existing outside state.\n')
        (self.output / 'skills').symlink_to(target, target_is_directory=True)
        result = self.generate()
        self.assertTrue(protected.is_file())
        self.assertEqual(protected.read_bytes(), b'Preserve existing outside state.\n')
        self.assertNotEqual(result.returncode, 0)

    def test_newline_in_a_source_filename_cannot_import_an_external_file(self):
        docs = self.source / 'docs'
        docs.mkdir()
        (docs / 'innocent.md').write_text('Ordinary selected documentation.\n')
        private = self.root / 'private.txt'
        private_bytes = b'Synthetic private file outside the source.\n'
        private.write_bytes(private_bytes)
        crafted = docs / ('innocent.md\n' + str(private))
        crafted.parent.mkdir(parents=True)
        crafted.write_text('Selected file with a deceptive name.\n')
        self.scaffold(['docs'])
        result = self.generate()
        references = self.output / 'skills/fixture-docs/references'
        copied_private_files = [p for p in references.rglob('*') if p.is_file() and p.read_bytes() == private_bytes]
        self.assertEqual(copied_private_files, [])
        self.assertNotEqual(result.returncode, 0)

    def test_supplied_metadata_cannot_execute_shell_commands(self):
        for field in ['tool_name', 'source_url']:
            with self.subTest(field=field):
                self.output = self.root / f'generated-{field}'
                marker = self.root / f'executed-{field}'
                payload = (f'Fixture $(touch "{marker}")' if field == 'tool_name'
                           else f'https://example.invalid/\'; touch "{marker}"; #.git')
                self.scaffold(['README.md'], **{field: payload})
                self.assertFalse(marker.exists())
                result = self.generate()
                self.assertFalse(marker.exists())
                self.assertEqual(result.returncode, 0, result.stderr)
                generated = self.output / 'skills/fixture-docs/SKILL.md'
                self.assertIn(payload, generated.read_text())

    def test_metadata_and_document_paths_preserve_punctuation_and_literal_tokens(self):
        tool_name = 'O\'Reilly "$SDK" & __SOURCE_URL_RAW__ — 工具'
        source_url = 'https://example.invalid/a&b.git'
        doc = self.source / 'guide & examples.md'
        doc.write_bytes(b'Punctuation in a documentation path.\n')
        self.scaffold([doc.name], tool_name=tool_name, source_url=source_url)
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        skill = self.output / 'skills/fixture-docs'
        text = (skill / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn(tool_name, text)
        self.assertIn(source_url, text)
        description = next(line for line in text.splitlines() if line.startswith('description: '))
        self.assertIn(tool_name, json.loads(description.removeprefix('description: ')))
        self.assertEqual((skill / 'references' / doc.name).read_bytes(), doc.read_bytes())


if __name__ == '__main__':
    unittest.main()
