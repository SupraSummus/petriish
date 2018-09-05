import os

from unittest import TestCase

import petriish


class SequenceTestCase(TestCase):
    def test_empty(self):
        pattern = petriish.Sequence([])
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        self.assertEqual(state.status, petriish.Status.SUCCEEDED)


class AlternativeTestCase(TestCase):
    def test_empty(self):
        pattern = petriish.Alternative([])
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        self.assertEqual(state.status, petriish.Status.FAILED)


class ParallelizationTestCase(TestCase):
    def test_empty(self):
        pattern = petriish.Parallelization([])
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        self.assertEqual(state.status, petriish.Status.SUCCEEDED)


class RepetitionTestCase(TestCase):
    pass


class CommandTestCase(TestCase):
    def test_failure(self):
        pattern = petriish.Command('false')
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        state.process_ended(*os.wait())
        self.assertEqual(state.status, petriish.Status.FAILED)

    def test_success(self):
        pattern = petriish.Command('true')
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        state.process_ended(*os.wait())
        self.assertEqual(state.status, petriish.Status.SUCCEEDED)
