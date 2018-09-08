import logging
import subprocess
from collections import namedtuple
import threading


logger = logging.getLogger(__name__)


class WorkflowPattern:
    """A type o workflow pattern"""

    def instantiate(self):
        return self.State(
            pattern=self,
        )

    class State(threading.Thread):
        """Specific instance of worflow pattern"""

        def __init__(self, pattern, **kwargs):
            self.__pattern = pattern
            self.finished = threading.Event()
            self.__succeeded = None
            super().__init__(**kwargs)

        def run(self):
            self.__succeeded = self.execute()
            self.finished.set()

        def execute(self):
            raise NotImplementedError()

        @property
        def succeeded(self):
            if not self.finished.is_set():
                raise RuntimeError()
            return self.__succeeded

        @property
        def pattern(self):
            return self.__pattern


class Sequence(WorkflowPattern, namedtuple('Sequence', ('children'))):
    class State(WorkflowPattern.State):
        def execute(self):
            for child_pattern in self.pattern.children:
                child = child_pattern.instantiate()
                child.start()
                child.join()
                if not child.succeeded:
                    return False
            return True


class Parallelization(WorkflowPattern, namedtuple('Sequence', ('children'))):
    class State(WorkflowPattern.State):
        def execute(self):
            children = [
                child_pattern.instantiate()
                for child_pattern in self.pattern.children
            ]
            for child in children:
                child.start()
            for child in children:
                child.join()
            return all(child.succeeded for child in children)


class Alternative(WorkflowPattern, namedtuple('Sequence', ('children'))):
    class State(WorkflowPattern.State):
        def execute(self):
            children = [
                child_pattern.instantiate()
                for child_pattern in self.pattern.children
            ]
            for child in children:
                child.start()
            for child in children:
                child.join()
            return len([None for child in children if child.succeeded]) == 1


class Repetition(WorkflowPattern, namedtuple('Sequence', ('child', 'exit'))):
    class State(WorkflowPattern.State):
        def execute(self):
            while True:
                child = self.pattern.child.instantiate()
                exit = self.pattern.exit.instantiate()
                child.start()
                exit.start()
                child.join()
                exit.join()
                if child.succeeded and exit.succeeded:
                    return False
                if not child.succeeded and not exit.succeeded:
                    return False
                if not child.succeeded and exit.succeeded:
                    return True


class Command(WorkflowPattern, namedtuple('Sequence', ('command'))):
    class State(WorkflowPattern.State):
        def execute(self):
            logger.info("starting %s", self.pattern.command)
            process = subprocess.Popen(self.pattern.command)
            status = process.wait()
            logger.info("process %d exited with exit code %d", process.pid, status)
            return status == 0


def run_workflow_pattern(workflow_pattern):
    state = workflow_pattern.instantiate()
    state.start()
    state.join()
    return state.succeeded
