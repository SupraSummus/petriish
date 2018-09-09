import logging
import subprocess
from collections import namedtuple
import threading


logger = logging.getLogger(__name__)


class Result:
    def __init__(self, success, output=None):
        self.__success = success
        self.__output = output

    @property
    def success(self):
        return self.__success

    @property
    def output(self):
        return self.__output

    def __repr__(self):
        return 'Result(success={}, output={})'.format(
            repr(self.success),
            repr(self.output),
        )


class WorkflowPattern:
    """A type of workflow pattern"""

    def instantiate(self, input):
        return self.State(
            pattern=self,
            input=input,
        )

    def execute(self, input):
        """Override this method to customize workflow type behaviour.

        It should return result of the execution.
        """
        raise NotImplementedError()

    @property
    def input_type(self):
        raise NotImplementedError()

    @property
    def output_type(self):
        raise NotImplementedError()

    def type_errors(self):
        raise NotImplementedError()

    class State(threading.Thread):
        """Specific instance of worfklow pattern"""

        def __init__(self, pattern, input, **kwargs):
            self.__pattern = pattern
            self.__input = input
            self.__finished = threading.Event()
            self.__result = None
            super().__init__(**kwargs)

        def run(self):
            self.__result = self.__pattern.execute(self.__input)
            self.__finished.set()

        @property
        def result(self):
            if not self.__finished.is_set():
                raise RuntimeError()
            return self.__result

        @property
        def succeeded(self):
            return self.result.success

        @property
        def finished(self):
            return self.__finished.is_set()

        @property
        def pattern(self):
            return self.__pattern


class Sequence(WorkflowPattern, namedtuple('Sequence', ('children'))):
    def execute(self, input):
        for child_pattern in self.children:
            result = run_workflow_pattern(child_pattern, input)
            if not result.success:
                return result
            input = result.output
        return Result(success=True, output=input)

    @property
    def input_type(self):
        pass

class Parallelization(WorkflowPattern, namedtuple('Parallelization', ('children'))):
    def execute(self, input):
        results = run_workflow_patterns({
            k: (v, input)
            for k, v in self.children.items()
        })
        return Result(
            success=all(r.success for r in results.values()),
            output={k: v.output for k, v in results.items()},
        )

    def input_type(self):
        return self. mm

class Alternative(WorkflowPattern, namedtuple('Alternative', ('children'))):
    def execute(self, input):
        results = run_workflow_patterns({
            i: (v, input)
            for i, v in enumerate(self.children)
        })
        results_ok = [
            result
            for result in results.values()
            if result.success
        ]
        if len(results_ok) == 1:
            return results_ok[0]
        else:
            return Result(success=False)


class Repetition(WorkflowPattern, namedtuple('Repetition', ('child', 'exit'))):
    def execute(self, input):
        while True:
            results = run_workflow_patterns({
                'child': (self.child, input),
                'exit': (self.exit, input),
            })
            child_success = results['child'].success
            exit_success = results['exit'].success
            if child_success and exit_success:
                return Result(success=False)
            if not child_success and not exit_success:
                return Result(success=False)
            if not child_success and exit_success:
                return results['exit']
            input = results['child'].output


class Command(WorkflowPattern, namedtuple('Command', ('command'))):
    def execute(self, input):
        logger.info("starting %s", self.command)
        process = subprocess.run(
            self.command,
            input=input,
            stdout=subprocess.PIPE,
        )
        logger.info("command %s exited with code %d", self.command, process.returncode)
        return Result(
            success=(process.returncode == 0),
            output=process.stdout,
        )


def run_workflow_patterns(patterns):
    states = {
        k: pattern.instantiate(input)
        for k, (pattern, input) in patterns.items()
    }
    for state in states.values():
        state.start()
    for state in states.values():
        state.join()
    return {k: state.result for k, state in states.items()}


def run_workflow_pattern(workflow_pattern, input):
    return run_workflow_patterns({None: (workflow_pattern, input)})[None]
