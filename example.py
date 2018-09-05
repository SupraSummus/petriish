import logging

from petriish import *



logging.basicConfig(level=30)


result = run_workflow_pattern(
    Sequence([
        Command(['echo', 'I have ability to count. Look at ma!']),
        Command(['echo', 'one']),
        Sequence([]),
        Command(['echo', 'two']),
        Repetition(
            child=Command(['false']),
            exit=Command(['true']),
        ),
        Command(['echo', 'three']),
        Alternative([
            Alternative([]),
            Command(['echo', '!']),
            Command(['false']),
        ]),

        Command(['echo', 'And now, ladies and gentelmen, a RACE!']),
        Parallelization([
            Sequence([
                Command(['sleep', '1']),
                Command(['echo', 'player A has completed the race']),
            ]),
            Sequence([
                Command(['sleep', '1']),
                Command(['echo', 'player B has completed the race']),
            ]),
            Sequence([
                Command(['sleep', '1']),
                Command(['echo', 'player C has completed the race']),
            ]),
        ]),
    ])
)

assert result == Status.SUCCEEDED
