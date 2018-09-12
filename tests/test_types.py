from unittest import TestCase
from petriish.types import Resolver, TypeResolutionError, PolymorphicType, Record, Bytes


class TypesTestCase(TestCase):
    def setUp(self):
        self.resolver = Resolver()

    def test_identity_bind(self):
        x = PolymorphicType()
        self.assertEqual(self.resolver.get_best_bind(x), x)

    def test_unify_with_self(self):
        x = PolymorphicType()
        self.resolver.unify(x, x)
        self.assertEqual(self.resolver.get_best_bind(x), x)

    def test_unify(self):
        x = PolymorphicType()
        self.resolver.unify(x, Bytes())
        self.assertEqual(self.resolver.get_best_bind(x), Bytes())

    def test_unify_in_record(self):
        x = PolymorphicType()
        y = PolymorphicType()
        self.resolver.unify(
            Record({'a': x, 'b': Record()}),
            Record({'a': Bytes(), 'b': y}),
        )
        self.assertEqual(self.resolver.get_best_bind(x), Bytes())
        self.assertEqual(self.resolver.get_best_bind(y), Record())

    def test_unify_variables(self):
        x = PolymorphicType()
        y = PolymorphicType()
        z = PolymorphicType()
        self.resolver.unify(x, y)
        self.resolver.unify(y, z)
        self.assertEqual(self.resolver.get_best_bind(x), self.resolver.get_best_bind(y))
        self.assertEqual(self.resolver.get_best_bind(z), self.resolver.get_best_bind(y))
        self.assertIn(self.resolver.get_best_bind(x), [x, y, z])

        # just to make sure it wont throw
        self.resolver.unify(z, x)
        self.resolver.unify(x, y)

    def test_reuse_resolver(self):
        x = PolymorphicType()
        y = PolymorphicType()

        self.resolver.unify(x, y)
        self.resolver.unify(y, Record())
        self.assertEqual(self.resolver.get_best_bind(x), Record())

        r = Resolver()
        r.unify(x, y)
        r.unify(x, Record())
        self.assertEqual(r.get_best_bind(y), Record())

    def test_reuse_resolver_2(self):
        x = PolymorphicType()
        y = PolymorphicType()

        self.resolver.unify(x, Record())
        self.resolver.unify(x, y)
        self.assertEqual(self.resolver.get_best_bind(y), Record())

        r = Resolver()
        r.unify(y, Record())
        r.unify(x, y)
        self.assertEqual(r.get_best_bind(x), Record())

    def test_fail_on_recursive_type(self):
        x = PolymorphicType()
        with self.assertRaises(TypeResolutionError):
            self.resolver.unify(x, Record({'aaa': x}))
        self.assertEqual(self.resolver.get_best_bind(x), x)

    def test_fail_on_reuse_resolver(self):
        x = PolymorphicType()
        self.resolver.unify(x, Record())
        with self.assertRaises(TypeResolutionError):
            self.resolver.unify(x, Bytes())
        self.assertEqual(self.resolver.get_best_bind(x), Record())
