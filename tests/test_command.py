from unittest import TestCase
import subprocess
import tempfile


class PetriishCommandTestCase(TestCase):
    def test_success(self):
        with tempfile.NamedTemporaryFile('w+t') as f:
            yml = "\n".join([
                "type: parallelization",
                "children:",
                "  - type: command",
                "    command: [echo, aaa]",
                "  - type: command",
                "    command: [echo, bbb]",
                "",
            ])
            f.write(yml)
            f.flush()
            result = subprocess.run(
                ['bin/petriish', f.name],
                stdout=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(
                sorted(result.stdout.decode('utf8').strip().split('\n')),
                ['aaa', 'bbb'],
            )

