import logging
import subprocess

from petriish import WorkflowPattern, Result
from petriish.types import Bytes, Record


logger = logging.getLogger(__name__)


class SimpleCommand(WorkflowPattern):
    def __init__(self, command, pass_stdin=False, capture_stdout=False, **kwargs):
        self.command = command
        self.pass_stdin = pass_stdin
        self.capture_stdout = capture_stdout
        super().__init__(**kwargs)

    def execute(self, input):
        kwargs = {}
        if self.pass_stdin:
            kwargs['input'] = input
        if self.capture_stdout:
            kwargs['stdout'] = subprocess.PIPE
        logger.info("starting %s", self.command)
        process = subprocess.run(self.command, **kwargs)
        logger.info("command %s exited with code %d", self.command, process.returncode)
        return Result(
            success=(process.returncode == 0),
            output=process.stdout,
        )

    def output_type(self, resolver, input_type):
        if self.pass_stdin:
            resolver.unify(input_type, Bytes())
        else:
            resolver.unify(input_type, Record())
        if self.capture_stdout:
            return Bytes()
        else:
            return Record()

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.command == other.command and
            self.pass_stdin == other.pass_stdin and
            self.capture_stdout == other.capture_stdout
        )

    def __hash__(self):
        return hash((
            self.command,
            self.pass_stdin,
            self.capture_stdout,
        ))
