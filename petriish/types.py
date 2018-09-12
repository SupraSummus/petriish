class TypeResolutionError(Exception):
    pass


class Resolver:
    @classmethod
    def is_polymorphic(cls, t):
        return isinstance(t, PolymorphicType)

    def __init__(self):
        self._binds = {}  # dict polymorphic -> its best bind

    def unify(self, a, b):
        if self.is_polymorphic(a):
            return self._bind(a, b)

        if self.is_polymorphic(b):
            return self._bind(b, a)

        return a.unify_with(self, b)

    def _bind(self, polymorphic_type, value_type):
        assert self.is_polymorphic(polymorphic_type)

        if self.is_polymorphic(value_type):
            if polymorphic_type == value_type:
                return polymorphic_type

            # always bind larger one to smaller one
            if id(polymorphic_type) < id(value_type):
                polymorphic_type, value_type = value_type, polymorphic_type

        if polymorphic_type in self._binds:
            self._binds[polymorphic_type] = self.unify(self._binds[polymorphic_type], value_type)
        else:
            if polymorphic_type in value_type.polymorphic_set:
                raise TypeResolutionError('couldnt make recursive bind {} = {}'.format(
                    polymorphic_type, value_type,
                ))
            self._binds[polymorphic_type] = value_type

        return self._binds[polymorphic_type]

    def get_best_bind(self, t):
        if t in self._binds:
            self._binds[t] = self.get_best_bind(self._binds[t])
            return self._binds[t]
        else:
            return t


class Type:
    def unify_with(self, resolver, other):
        raise NotImplementedError()

    @property
    def polymorphic_set(self):
        """Set of all PolymorphicType instances inside this type"""
        raise NotImplementedError()


class PolymorphicType(Type):
    def __hash__(self):
        return id(self)

    @property
    def polymorphic_set(self):
        return set([self])


class Record(Type):
    def __init__(self, fields={}):
        self.fields = fields

    def unify_with(self, resolver, other):
        if not isinstance(other, self.__class__):
            raise TypeResolutionError('cannot unify {} with {}'.format(
                self, other,
            ))
        if self.fields.keys() != other.fields.keys():
            raise TypeResolutionError()
        return Record({
            k: resolver.unify(v, other.fields[k])
            for k, v in self.fields.items()
        })

    @property
    def polymorphic_set(self):
        s = set()
        for v in self.fields.values():
            s.update(v.polymorphic_set)
        return s

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.fields == other.fields

    def __hash__(self):
        return hash(tuple(self.fields.items()))

    def __repr__(self):
        return 'Record({})'.format(repr(self.fields))


class Bytes(Type):
    def unify_with(self, resolver, other):
        if not isinstance(other, self.__class__):
            raise TypeError('cannot unify {} with {}'.format(self, other))
        return self

    @property
    def polymorphic_set(self):
        return set()

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return hash(self.__class__)

    def __repr__(self):
        return 'Bytes()'
