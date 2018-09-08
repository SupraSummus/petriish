import threading
from unittest import TestCase

import petriish


class DummyCommand(petriish.WorkflowPattern):
    def __init__(self, **kwargs):
        self.result = None
        self.semaphore = threading.Semaphore(value=0)
        self.feedback_semaphore = threading.Semaphore(value=0)

    def trigger(self, result):
        self.result = result
        self.semaphore.release()
        self.feedback_semaphore.acquire()

    class State(petriish.WorkflowPattern.State):
        def execute(self):
            self.pattern.semaphore.acquire()
            return self.pattern.result

        def run(self):
            super().run()
            self.pattern.feedback_semaphore.release()


class WorkflowPatternAssertsMixin:
    def assertNotFinished(self, state):
        self.assertFalse(state.finished.is_set())
        with self.assertRaises(RuntimeError):
            state.succeeded

    def assertSucceeded(self, state):
        state.join(timeout=1)
        self.assertTrue(state.finished.is_set())
        self.assertTrue(state.succeeded)

    def assertFailed(self, state):
        state.join(timeout=1)
        self.assertTrue(state.finished.is_set())
        self.assertFalse(state.succeeded)


class SequenceTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_empty(self):
        pattern = petriish.Sequence([])
        state = pattern.instantiate()

        self.assertNotFinished(state)
        state.start()
        self.assertSucceeded(state)

    def test_subworkflows(self):
        sub_a = DummyCommand(name='a')
        sub_b = DummyCommand(name='b')
        pattern = petriish.Sequence([sub_a, sub_b])
        state = pattern.instantiate()

        self.assertNotFinished(state)
        state.start()
        self.assertNotFinished(state)
        sub_a.trigger(True)
        self.assertNotFinished(state)
        sub_b.trigger(False)
        self.assertFailed(state)


class AlternativeTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_empty(self):
        pattern = petriish.Alternative([])
        state = pattern.instantiate()

        self.assertNotFinished(state)
        state.start()
        self.assertFailed(state)


class ParallelizationTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_empty(self):
        pattern = petriish.Parallelization([])
        state = pattern.instantiate()

        self.assertNotFinished(state)
        state.start()
        self.assertSucceeded(state)


class RepetitionTestCase(TestCase, WorkflowPatternAssertsMixin):
    def setUp(self):
        self.child = DummyCommand()
        self.exit = DummyCommand()
        self.pattern = petriish.Repetition(
            child=self.child,
            exit=self.exit,
        )
        self.state = self.pattern.instantiate()

        self.assertNotFinished(self.state)
        self.state.start()
        self.assertNotFinished(self.state)

    def test_success(self):
        self.exit.trigger(True)
        self.assertNotFinished(self.state)
        self.child.trigger(False)
        self.assertSucceeded(self.state)

    def test_loop(self):
        self.exit.trigger(False)
        self.assertNotFinished(self.state)
        self.child.trigger(True)
        self.assertNotFinished(self.state)

        # allow for thread termination
        self.exit.trigger(True)
        self.child.trigger(False)

    def test_fail_both(self):
        self.exit.trigger(False)
        self.assertNotFinished(self.state)
        self.child.trigger(False)
        self.assertFailed(self.state)

    def test_fail_none(self):
        self.exit.trigger(True)
        self.assertNotFinished(self.state)
        self.child.trigger(True)
        self.assertFailed(self.state)


class CommandTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_failure(self):
        pattern = petriish.Command('false')
        state = pattern.instantiate()
        self.assertNotFinished(state)
        state.start()
        self.assertFailed(state)

    def test_success(self):
        pattern = petriish.Command('true')
        state = pattern.instantiate()
        self.assertNotFinished(state)
        state.start()
        self.assertSucceeded(state)
