from unittest import TestCase

import petriish
from petriish.serialization import deserialize
from petriish.patterns.posix import SimpleCommand


class DeserializationTestCase(TestCase):
    def _test_deserialize_list(self, type, constructor):
        self.assertEqual(
            deserialize({
                'type': type,
                'children': [
                    {'type': 'sequence', 'children': []},
                    {'type': 'sequence', 'children': []},
                ],
            }),
            constructor([
                petriish.Sequence([]),
                petriish.Sequence([]),
            ]),
        )

    def test_deserialize_sequence(self):
        self._test_deserialize_list('sequence', petriish.Sequence)

    def test_deserialize_alternative(self):
        self._test_deserialize_list('alternative', petriish.Alternative)

    def test_deserialize_parallelization(self):
        self.assertEqual(
            deserialize({
                'type': 'parallelization',
                'children': {
                    'aaa': {'type': 'sequence', 'children': []},
                    'bbb': {'type': 'sequence', 'children': []},
                },
            }),
            petriish.Parallelization({
                'aaa': petriish.Sequence([]),
                'bbb': petriish.Sequence([]),
            }),
        )

    def test_deserialize_repetition(self):
        self.assertEqual(
            deserialize({
                'type': 'repetition',
                'child': {'type': 'sequence', 'children': []},
                'exit': {'type': 'alternative', 'children': []},
            }),
            petriish.Repetition(
                child=petriish.Sequence([]),
                exit=petriish.Alternative([]),
            ),
        )

    def test_deserialize_command(self):
        self.assertEqual(
            deserialize({
                'type': 'command',
                'command': ['echo', 'a', 'b', 'c'],
            }),
            SimpleCommand(
                command=['echo', 'a', 'b', 'c'],
                pass_stdin=False,
                capture_stdout=False,
            ),
        )
