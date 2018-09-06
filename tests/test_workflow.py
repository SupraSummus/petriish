import os

from unittest import TestCase

import petriish


class DummyCommand(petriish.WorkflowPattern, petriish.attr('dummy_pid', default=0)):
    class State(petriish.WorkflowPattern.State):
        def __init__(self, *args, **kwargs):
            self._status = petriish.Status.NEW
            super().__init__(*args, **kwargs)

        def start(self):
            assert self._status == petriish.Status.NEW
            self._status = petriish.Status.RUNNING

        def process_ended(self, pid, status):
            if pid == self.pattern.dummy_pid:
                assert self._status == petriish.Status.RUNNING
                self._status = status

        @property
        def status(self):
            return self._status


class SequenceTestCase(TestCase):
    def test_empty(self):
        pattern = petriish.Sequence([])
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        self.assertEqual(state.status, petriish.Status.SUCCEEDED)

    def test_subworkflows(self):
        pattern = petriish.Sequence([
            DummyCommand(dummy_pid='a'),
            DummyCommand(dummy_pid='b'),
        ])
        state = pattern.instantiate()
        self.assertEqual(state.status, petriish.Status.NEW)
        state.start()
        self.assertEqual(state.status, petriish.Status.RUNNING)
        state.process_ended('a', petriish.Status.SUCCEEDED)
        self.assertEqual(state.status, petriish.Status.RUNNING)
        state.process_ended('b', petriish.Status.FAILED)
        self.assertEqual(state.status, petriish.Status.FAILED)


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
    def setUp(self):
        self.pattern = petriish.Repetition(
            child=DummyCommand(dummy_pid='child'),
            exit=DummyCommand(dummy_pid='exit'),
        )
        self.state = self.pattern.instantiate()

    def assertStatus(self, status):
        self.assertEqual(self.state.status, status)

    def test_new(self):
        self.assertStatus(petriish.Status.NEW)
        self.state.start()
        self.assertStatus(petriish.Status.RUNNING)

    def test_success(self):
        self.state.start()
        self.state.process_ended('exit', petriish.Status.SUCCEEDED)
        self.assertStatus(petriish.Status.RUNNING)
        self.state.process_ended('child', petriish.Status.FAILED)
        self.assertStatus(petriish.Status.SUCCEEDED)

    def test_loop(self):
        self.state.start()
        self.state.process_ended('exit', petriish.Status.FAILED)
        self.assertStatus(petriish.Status.RUNNING)
        self.state.process_ended('child', petriish.Status.SUCCEEDED)
        self.assertStatus(petriish.Status.RUNNING)

    def test_fail_both(self):
        self.state.start()
        self.state.process_ended('exit', petriish.Status.FAILED)
        self.assertStatus(petriish.Status.RUNNING)
        self.state.process_ended('child', petriish.Status.FAILED)
        self.assertStatus(petriish.Status.FAILED)

    def test_fail_none(self):
        self.state.start()
        self.state.process_ended('exit', petriish.Status.SUCCEEDED)
        self.assertStatus(petriish.Status.RUNNING)
        self.state.process_ended('child', petriish.Status.SUCCEEDED)
        self.assertStatus(petriish.Status.FAILED)


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
