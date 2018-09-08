import logging
import subprocess
from collections import namedtuple
import threading


logger = logging.getLogger(__name__)


class WorkflowPattern:
    """A type of workflow pattern"""

    def instantiate(self):
        return self.State(
            pattern=self,
        )

    def execute(self):
        """Override this method to customize workflow type behaviour.

        It should return weather the execution has been successful (bool).
        """
        raise NotImplementedError()

    class State(threading.Thread):
        """Specific instance of worfklow pattern"""

        def __init__(self, pattern, **kwargs):
            self.__pattern = pattern
            self.__finished = threading.Event()
            self.__succeeded = None
            super().__init__(**kwargs)

        def run(self):
            self.__succeeded = self.__pattern.execute()
            self.__finished.set()

        @property
        def succeeded(self):
            if not self.__finished.is_set():
                raise RuntimeError()
            return self.__succeeded

        @property
        def finished(self):
            return self.__finished.is_set()

        @property
        def pattern(self):
            return self.__pattern


class Sequence(WorkflowPattern, namedtuple('Sequence', ('children'))):
    def execute(self):
        for child_pattern in self.children:
            success = run_workflow_pattern(child_pattern)
            if not success:
                return False
        return True


class Parallelization(WorkflowPattern, namedtuple('Parallelization', ('children'))):
    def execute(self):
        return all(run_workflow_patterns(self.children))


class Alternative(WorkflowPattern, namedtuple('Alternative', ('children'))):
    def execute(self):
        return len([
            None
            for success in run_workflow_patterns(self.children)
            if success
        ]) == 1


class Repetition(WorkflowPattern, namedtuple('Repetition', ('child', 'exit'))):
    def execute(self):
        while True:
            child_success, exit_success = run_workflow_patterns([
                self.child,
                self.exit,
            ])
            if child_success and exit_success:
                return False
            if not child_success and not exit_success:
                return False
            if not child_success and exit_success:
                return True


class Command(WorkflowPattern, namedtuple('Command', ('command'))):
    def execute(self):
        logger.info("starting %s", self.command)
        process = subprocess.Popen(self.command)
        status = process.wait()
        logger.info("process %d exited with exit code %d", process.pid, status)
        return status == 0


def run_workflow_patterns(patterns):
    states = [pattern.instantiate() for pattern in patterns]
    for state in states:
        state.start()
    for state in states:
        state.join()
    return [state.succeeded for state in states]


def run_workflow_pattern(workflow_pattern):
    return run_workflow_patterns([workflow_pattern])[0]
