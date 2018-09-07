def attr(name, default=None, required=False):
    """Mixin that has specified attr settable in constructor and then readonly."""
    private_name = '_' + name

    class AttrMixin:
        def __init__(self, *args, **kwargs):
            if name in kwargs:  # value is in kwargs
                value = kwargs[name]
                del kwargs[name]

            elif len(args) > 0:  # value is in args
                args = list(args)
                value = args.pop()

            elif not required:  # fallback to default value
                value = default

            else:  # value is required but not supplied
                raise TypeError('required argument \'{}\' not found'.format(name))

            setattr(self, private_name, value)
            super().__init__(*args, **kwargs)

        def __eq__(self, other):
            return (
                hasattr(other, name) and
                getattr(other, name) == getattr(other, name) and
                super().__eq__(other)
            )

    setattr(AttrMixin, name, property(lambda self: getattr(self, private_name)))

    return AttrMixin


def without_key(d, key):
    return {
        k: v for k, v in d.items()
        if k != key
    }
