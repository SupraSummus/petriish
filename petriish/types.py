class TypeResolutionError(Exception):
    pass


class Resolver:
    @classmethod
    def is_polymorphic(cls, t):
        return isinstance(t, PolymorphicType)

    def __init__(self):
        self._binds = {}  # dict polymorphic -> its best bind

    def unify(self, a, b):
        if self.is_polymorphic(b):
            a, b = b, a

        if self.is_polymorphic(a):
            a = self.get_best_bind(a)

            if self.is_polymorphic(a):
                return self._bind(a, b)

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
                self._binds[polymorphic_type] = self._bind(value_type, self._binds[polymorphic_type])
            else:
                self._binds[polymorphic_type] = value_type

        else:
            if polymorphic_type in self._binds:
                if self.is_polymorphic(self._binds[polymorphic_type]):
                    self._binds[polymorphic_type] = self._bind(self._binds[polymorphic_type], value_type)
                else:
                    raise TypeResolutionError('cannot bind {} with {} - {} is already {}'.format(
                        polymorphic_type, value_type,
                        polymorphic_type, self._binds[polymorphic_type],
                    ))
            else:
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
        for k in self.fields.keys():
            resolver.unify(self.fields[k], other.fields[k])

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.fields == other.fields

    def __hash__(self):
        return hash(tuple(self.fields.items()))


class Bytes(Type):
    def unify_with(self, resolver, other):
        if not isinstance(other, self.__class__):
            raise TypeError('cannot unify {} with {}'.format(self, other))

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return hash(self.__class__)
