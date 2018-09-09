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


def deserialize_dict_values(d):
    return {
        k: deserialize(v)
        for k, v in d.items()
    }


def id(a):
    return a


deserializers = {
    'sequence': list_deserializer(Sequence),
    'alternative': list_deserializer(Alternative),
    'parallelization': kwargs_deserializer(Parallelization, {
        'children': deserialize_dict_values,
    }),
    'repetition': kwargs_deserializer(Repetition, {
        'child': deserialize,
        'exit': deserialize,
    }),
    'command': kwargs_deserializer(Command, {
        'command': id,
    }),
}
