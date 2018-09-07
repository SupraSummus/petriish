from . import (
    Sequence, Alternative, Parallelization,
    Repetition, Command,
)
from .utils import without_key


def deserialize(obj):
    return deserializers[obj['type']](without_key(obj, 'type'))


def list_deserializer(constructor):
    def f(obj):
        return constructor(children=[
            deserialize(sub_obj)
            for sub_obj in obj['children']
        ])
    return f


def kwargs_deserializer(constructor, mapping):
    def f(obj):
        return constructor(**{
            k: mapping[k](v)
            for k, v in obj.items()
        })
    return f


id = lambda a: a


deserializers = {
    'sequence': list_deserializer(Sequence),
    'alternative': list_deserializer(Alternative),
    'parallelization': list_deserializer(Parallelization),
    'repetition': kwargs_deserializer(Repetition, {
        'child': deserialize,
        'exit': deserialize,
    }),
    'command': kwargs_deserializer(Command, {
        'command': id,
    }),
}
