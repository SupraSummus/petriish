from unittest import TestCase

import petriish
from petriish.serialization import deserialize


class DeserializationTestCase(TestCase):
    def _test_deserialize_list(self, type, constructor):
        self.assertEqual(
            deserialize({
                'type': 'sequence',
                'children': [
                    {'type': 'sequence', 'children': []},
                    {'type': 'sequence', 'children': []},
                ],
            }),
            petriish.Sequence([
                petriish.Sequence([]),
                petriish.Sequence([]),
            ]),
        )

    def test_deserialize_sequence(self):
        self._test_deserialize_list('sequence', petriish.Sequence)

    def test_deserialize_alternative(self):
        self._test_deserialize_list('alternative', petriish.Alternative)

    def test_deserialize_parallelization(self):
        self._test_deserialize_list('parallelization', petriish.Parallelization)

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
            petriish.Command(
                command=['echo', 'a', 'b', 'c'],
            ),
        )
