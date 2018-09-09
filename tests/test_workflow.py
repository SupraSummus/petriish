import threading
from unittest import TestCase

import petriish


class DummyCommand(petriish.WorkflowPattern):
    def __init__(self, **kwargs):
        self.__dummy_result = None
        self.__dummy_result_semaphore = threading.Semaphore(value=0)
        self.__feedback = None
        self.__feedback_semaphore = threading.Semaphore(value=0)

    def trigger(self, result):
        self.__feedback_semaphore.acquire()
        self.__dummy_result = result
        self.__dummy_result_semaphore.release()
        return self.__feedback

    def execute(self, input):
        self.__feedback = input
        self.__feedback_semaphore.release()
        self.__dummy_result_semaphore.acquire()
        return self.__dummy_result


class WorkflowPatternAssertsMixin:
    def assertNotFinished(self, state):
        self.assertFalse(state.finished)
        with self.assertRaises(RuntimeError):
            state.succeeded

    def assertSucceeded(self, state, output):
        state.join(timeout=1)
        self.assertTrue(state.finished)
        self.assertTrue(state.succeeded)
        self.assertTrue(state.result.success)
        self.assertEqual(state.result.output, output)

    def assertFailed(self, state):
        state.join(timeout=1)
        self.assertTrue(state.finished)
        self.assertFalse(state.succeeded)
        self.assertFalse(state.result.success)


class SequenceTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_empty(self):
        pattern = petriish.Sequence([])
        state = pattern.instantiate('blah')

        self.assertNotFinished(state)
        state.start()
        self.assertSucceeded(state, 'blah')

    def test_subworkflows(self):
        sub_a = DummyCommand(name='a')
        sub_b = DummyCommand(name='b')
        pattern = petriish.Sequence([sub_a, sub_b])
        state = pattern.instantiate('in')

        self.assertNotFinished(state)
        state.start()
        self.assertNotFinished(state)
        self.assertEqual(sub_a.trigger(petriish.Result(True, 'a out')), 'in')
        self.assertNotFinished(state)
        self.assertEqual(sub_b.trigger(petriish.Result(False)), 'a out')
        self.assertFailed(state)


class AlternativeTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_empty(self):
        pattern = petriish.Alternative([])
        state = pattern.instantiate('ble')

        self.assertNotFinished(state)
        state.start()
        self.assertFailed(state)


class ParallelizationTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_empty(self):
        pattern = petriish.Parallelization({})
        state = pattern.instantiate('ble')

        self.assertNotFinished(state)
        state.start()
        self.assertSucceeded(state, {})


class RepetitionTestCase(TestCase, WorkflowPatternAssertsMixin):
    def setUp(self):
        self.child = DummyCommand()
        self.exit = DummyCommand()
        self.pattern = petriish.Repetition(
            child=self.child,
            exit=self.exit,
        )
        self.state = self.pattern.instantiate('in')

        self.assertNotFinished(self.state)
        self.state.start()
        self.assertNotFinished(self.state)

    def test_success(self):
        self.assertEqual(self.exit.trigger(petriish.Result(True, 'exit out')), 'in')
        self.assertNotFinished(self.state)
        self.assertEqual(self.child.trigger(petriish.Result(False)), 'in')
        self.assertSucceeded(self.state, 'exit out')

    def test_loop(self):
        self.assertEqual(self.exit.trigger(petriish.Result(False)), 'in')
        self.assertNotFinished(self.state)
        self.assertEqual(self.child.trigger(petriish.Result(True, 'child out')), 'in')
        self.assertNotFinished(self.state)

        # second loop
        self.assertEqual(self.exit.trigger(petriish.Result(True, 'exit out')), 'child out')
        self.assertEqual(self.child.trigger(petriish.Result(False)), 'child out')

    def test_fail_both(self):
        self.assertEqual(self.exit.trigger(petriish.Result(False)), 'in')
        self.assertNotFinished(self.state)
        self.assertEqual(self.child.trigger(petriish.Result(False)), 'in')
        self.assertFailed(self.state)

    def test_fail_none(self):
        self.assertEqual(self.exit.trigger(petriish.Result(True, 'exit out')), 'in')
        self.assertNotFinished(self.state)
        self.assertEqual(self.child.trigger(petriish.Result(True, 'child out')), 'in')
        self.assertFailed(self.state)


class CommandTestCase(TestCase, WorkflowPatternAssertsMixin):
    def test_failure(self):
        pattern = petriish.Command('false')
        state = pattern.instantiate('')
        self.assertNotFinished(state)
        state.start()
        self.assertFailed(state)

    def test_success(self):
        pattern = petriish.Command('true')
        state = pattern.instantiate('')
        self.assertNotFinished(state)
        state.start()
        self.assertSucceeded(state, b'')
