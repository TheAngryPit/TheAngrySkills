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

    def scaffold(self, paths):
        command = ['bash', str(CREATE), '--name', 'fixture-docs', '--tool-name', 'Fixture',
                   '--source-url', 'https://example.invalid/fixture.git', '--output', str(self.output)]
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
        self.scaffold(['README.md', 'INDEX.md'])
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        references = self.output / 'skills/fixture-docs/references'
        self.assertEqual((references / 'README.md').read_bytes(), b'Synthetic documentation.\n')
        self.assertEqual((references / 'INDEX.source.md').read_bytes(), original)
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


if __name__ == '__main__':
    unittest.main()
