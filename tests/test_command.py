from unittest import TestCase
import subprocess
import tempfile


class PetriishCommandTestCase(TestCase):
    def test_success(self):
        with tempfile.NamedTemporaryFile('w+t') as f:
            yml = "\n".join([
                "type: parallelization",
                "children:",
                "  a:",
                "    type: command",
                "    command: [echo, aaa]",
                "  b:",
                "    type: command",
                "    command: [echo, bbb]",
                "",
            ])
            f.write(yml)
            f.flush()
            result = subprocess.run(
                ['bin/petriish', f.name],
                input='',
                stdout=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(
                eval(result.stdout),
                {'a': b'aaa\n', 'b': b'bbb\n'},
            )
