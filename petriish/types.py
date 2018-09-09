class TypeError(Exception):
    pass


class Resolver:
    def __init__(self):
        self._binds = {}  # dict polymorphic -> its best bind

    def unify(self, a, b):
        if isinstance(a, PolymorphicType) and isinstance(b, PolymorphicType):
            a = self._get_best_bind(a)
            b = self._get_best_bind(b)

            if not isinstance(a, PolymorphicType) or not isinstance(b, PolymorphicType):
                # at least one of them is already bound
                return self.unify(a, b)

            return self._bind(a, b)

        if isinstance(a, PolymorphicType):
            a = self._get_best_bind(a)
            # it's already bound
            if not isinstance(a, PolymorphicType):
                return self.unify(a, b)
            return self._bind(a, b)

        if isinstance(b, PolymorphicType):
            return self.unify(b, a)

        return a.unify_with(self, b)

    def _bind(self, polymorphic_type, value_type):
        assert isinstance(polymorphic_type, PolymorphicType)

        if isinstance(value_type, PolymorphicType):
            value_type, polymorphic_type = sorted([polymorphic_type, value_type], key=id)

            if polymorphic_type in self._binds:
                self._binds[polymorphic_type] = self._bind(value_type, self._binds[polymorphic_type])
            else:
                self._binds[polymorphic_type] = value_type

        else:
            if polymorphic_type in self._binds:
                if isinstance(self._binds[polymorphic_type], PolymorphicType):
                    self._binds[polymorphic_type] = self._bind(self._binds[polymorphic_type], value_type)
                else:
                    raise TypeError('cannot bind {} with {} - {} is already {}'.format(
                        polymorphic_type, value_type,
                        polymorphic_type, self._binds[polymorphic_type],
                    ))
            else:
                self._binds[polymorphic_type] = value_type

        return self._binds[polymorphic_type]

    def _get_best_bind(self, t):
        if t in self._binds:
            self._binds[t] = self._get_best_bind(self._binds[t])
            return self._binds[t]
        else:
            return t


class Type:
    def unify_with(self, resolver, other):
        raise NotImplementedError()


class PolymorphicType(Type):
    def __hash__(self):
        return id(self)


class Record(Type):
    def __init__(self, fields={}):
        self.fields = fields

    def unify_with(self, resolver, other):
        if not isinstance(other, self.__class__):
            raise TypeError()
        if self.fields.keys() != other.fields.keys():
            raise TypeError()
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
