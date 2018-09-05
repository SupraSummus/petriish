import os
import logging
import subprocess
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


def attr(name):
    """ Mixin that has specified attr settable in constructor and then readonly. """
    private_name = '_' + name
    class AttrMixin:
        def __init__(self, *args, **kwargs):
            if len(args) == 0:
                setattr(self, private_name, kwargs[name])
                del kwargs[name]
            else:
                args = list(args)
                setattr(self, private_name, args.pop())
            super().__init__(*args, **kwargs)
    setattr(AttrMixin, name, property(lambda self: getattr(self, private_name)))
    return AttrMixin


class Status(Enum):
    NEW = 1
    RUNNING = 2
    SUCCEEDED = 3
    FAILED = 4


class WorkflowPattern:
    def instantiate(self):
        return self.State(
            pattern=self,
        )

    class State(attr('pattern')):
        def start(self):
            raise NotImplementedError()

        def process_ended(self, pid, status):
            """ Call to notify that a process has ended. """
            raise NotImplementedError()

        @property
        def status(self):
            raise NotImplementedError()


class Sequence(WorkflowPattern, attr('children')):
    class State(WorkflowPattern.State):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._next_child = 0
            self._child_state = None

        def start(self):
            self._start_child()

        def process_ended(self, pid, status):
            if self._child_state is None:
                return
            self._child_state.process_ended(pid, status)
            if self._child_state.status == Status.SUCCEEDED:
                self._start_child()

        @property
        def status(self):
            if self._child_state is not None:
                return self._child_state.status
            if self._next_child >= len(self.pattern.children):
                return Status.SUCCEEDED
            return Status.NEW

        def _start_child(self):
            while True:
                if self._next_child >= len(self.pattern.children):
                    self._child_state = None
                    return
                self._child_state = self.pattern.children[self._next_child].instantiate()
                self._next_child += 1
                self._child_state.start()
                if self._child_state.status != Status.SUCCEEDED:
                    return


class Parallelization(WorkflowPattern, attr('children')):
    class State(WorkflowPattern.State):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._children_states = None

        def start(self):
            assert self._children_states is None
            self._children_states = [
                child.instantiate()
                for child in self.pattern.children
            ]
            for s in self._children_states:
                s.start()

        def process_ended(self, pid, status):
            for c in self._children_states:
                c.process_ended(pid, status)

        @property
        def status(self):
            if self._children_states is None:
                return Status.NEW

            counts = Counter(c.status for c in self._children_states)
            all_count = len(self.pattern.children)
            if counts[Status.SUCCEEDED] == all_count:
                return Status.SUCCEEDED

            if counts[Status.NEW] == all_count:
                return Status.NEW
            assert counts[Status.NEW] == 0

            if counts[Status.RUNNING] > 0:
                return Status.RUNNING
            assert counts[Status.SUCCEEDED] + counts[Status.FAILED] == all_count

            if counts[Status.FAILED] > 0:
                return Status.FAILED
            assert False


class Alternative(WorkflowPattern, attr('children')):
    class State(WorkflowPattern.State):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._children_states = None

        def start(self):
            assert self._children_states is None
            self._children_states = [
                child.instantiate()
                for child in self.pattern.children
            ]
            for s in self._children_states:
                s.start()

        def process_ended(self, pid, status):
            for c in self._children_states:
                c.process_ended(pid, status)

        @property
        def status(self):
            if self._children_states is None:
                return Status.NEW

            counts = Counter(c.status for c in self._children_states)
            all_count = len(self.pattern.children)
            if all_count == 0:
                return Status.FAILED

            if counts[Status.NEW] == all_count:
                return Status.NEW
            assert counts[Status.NEW] == 0

            if counts[Status.RUNNING] > 0:
                return Status.RUNNING
            assert counts[Status.SUCCEEDED] + counts[Status.FAILED] == all_count

            if counts[Status.SUCCEEDED] == 1:
                return Status.SUCCEEDED
            else:
                return Status.FAILED


class Repetition(WorkflowPattern, attr('child'), attr('exit')):
    class State(WorkflowPattern.State):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._child_state = None
            self._exit_state = None

        def start(self):
            self._child_state = self.pattern.child.instantiate()
            self._child_state.start()
            self._exit_state = self.pattern.exit.instantiate()
            self._exit_state.start()

        def process_ended(self, pid, status):
            self._child_state.process_ended(pid, status)
            self._exit_state.process_ended(pid, status)
            c = self._child_state.status
            e = self._exit_state.status
            if c == Status.SUCCEEDED and e == Status.FAILED:
                self.start()

        @property
        def status(self):
            if self._child_state is None:
                assert self._exit_state is None
                return Status.NEW
            c = self._child_state.status
            e = self._exit_state.status
            if c == Status.SUCCEEDED and e == Status.SUCCEEDED:
                return Status.FAILED
            if c == Status.FAILED and e == Status.FAILED:
                return Status.FAILED
            if c == Status.FAILED and e == Status.SUCCEEDED:
                return Status.SUCCEEDED
            if c == Status.RUNNING or e == Status.RUNNING:
                return Status.RUNNING
            assert False


class Command(WorkflowPattern, attr('command')):
    class State(WorkflowPattern.State):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._process = None

        def start(self):
            logger.info("starting %s", self.pattern.command)
            self._process = subprocess.Popen(self.pattern.command)

        def process_ended(self, pid, status):
            if pid == self._process.pid:
                self._process.poll()
                self._process.returncode = os.WEXITSTATUS(status)  # this is needed, apparently
                logger.info("process %d exited with exit code %d", pid, self._process.returncode)

        @property
        def status(self):
            if self._process is None:
                return Status.NEW
            if self._process.returncode is None:
                return Status.RUNNING
            if self._process.returncode == 0:
                return Status.SUCCEEDED
            else:
                return Status.FAILED

        @property
        def pids(self):
            if self._process is None:
                return set()
            if self._process.returncode is not None:
                return set()
            else:
                return {self._process.pid}


def run_workflow_pattern(workflow_pattern):
    state = workflow_pattern.instantiate()
    state.start()
    while state.status == Status.RUNNING:
        pid, exit_status = os.wait()
        state.process_ended(pid, exit_status)
    return state.status
